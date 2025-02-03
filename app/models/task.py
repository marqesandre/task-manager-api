from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import json
from bson import ObjectId
from marshmallow import Schema, fields, validate

from app.extensions import mongo, redis_client

CACHE_EXPIRATION = 300  # 5 minutes in seconds

class TaskStatus(str, Enum):
    """Task status enumeration."""
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'

class TaskSchema(Schema):
    """Task schema for validation and serialization."""
    _id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(required=True)
    status = fields.Str(
        required=True,
        validate=validate.OneOf([status.value for status in TaskStatus])
    )
    due_date = fields.DateTime(required=True)
    user_id = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class Task:
    """Task model for MongoDB."""
    
    def __init__(
        self,
        title: str,
        description: str,
        user_id: str,
        due_date: Optional[datetime] = None,
        status: str = "pending",
        _id: Optional[ObjectId] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.title = title
        self.description = description
        self.user_id = user_id
        self.due_date = due_date
        self.status = status
        self._id = _id if _id else ObjectId()
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        return {
            'id': str(self._id),
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'user_id': self.user_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def save(self) -> None:
        """Save task to database and update cache."""
        task_data = {
            '_id': self._id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'user_id': self.user_id,
            'due_date': self.due_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        mongo.db.tasks.insert_one(task_data)
        
        # Invalidate user's tasks cache
        redis_client.client.delete(f'tasks:{self.user_id}')

    @classmethod
    def get_by_id(cls, task_id: str, user_id: str) -> Optional['Task']:
        """Get a task by its ID and user ID with caching."""
        cache_key = f'task:{task_id}:{user_id}'
        cached_task = redis_client.client.get(cache_key)
        
        if cached_task:
            try:
                task_data = json.loads(cached_task)
                return cls(
                    title=task_data['title'],
                    description=task_data['description'],
                    user_id=task_data['user_id'],
                    status=task_data['status'],
                    due_date=datetime.fromisoformat(task_data['due_date']) if task_data['due_date'] else None,
                    _id=ObjectId(task_data['id']),
                    created_at=datetime.fromisoformat(task_data['created_at']),
                    updated_at=datetime.fromisoformat(task_data['updated_at'])
                )
            except (json.JSONDecodeError, KeyError):
                redis_client.client.delete(cache_key)

        try:
            task_data = mongo.db.tasks.find_one({
                '_id': ObjectId(task_id),
                'user_id': user_id
            })
            if not task_data:
                return None
                
            task = cls(**task_data)
            
            # Update cache
            redis_client.client.setex(
                cache_key,
                CACHE_EXPIRATION,
                json.dumps(task.to_dict())
            )
            
            return task
        except:
            return None

    @classmethod
    def get_user_tasks(cls, user_id: str) -> List['Task']:
        """Get all tasks for a specific user with caching."""
        # Try to get from cache first
        cache_key = f'tasks:{user_id}'
        cached_tasks = redis_client.client.get(cache_key)
        
        if cached_tasks:
            try:
                tasks_data = json.loads(cached_tasks)
                return [cls(
                    title=task['title'],
                    description=task['description'],
                    user_id=task['user_id'],
                    status=task['status'],
                    due_date=datetime.fromisoformat(task['due_date']) if task['due_date'] else None,
                    _id=ObjectId(task['id']),
                    created_at=datetime.fromisoformat(task['created_at']),
                    updated_at=datetime.fromisoformat(task['updated_at'])
                ) for task in tasks_data]
            except (json.JSONDecodeError, KeyError):
                # If there's any error parsing the cache, ignore it
                redis_client.client.delete(cache_key)

        # Get from database
        tasks_data = mongo.db.tasks.find({'user_id': user_id})
        tasks = [cls(**task_data) for task_data in tasks_data]
        
        # Update cache
        try:
            redis_client.client.setex(
                cache_key,
                CACHE_EXPIRATION,
                json.dumps([task.to_dict() for task in tasks])
            )
        except:
            # If caching fails, just ignore it
            pass
            
        return tasks

    def update(self, **kwargs) -> None:
        """Update task in database and update cache."""
        updates = {'updated_at': datetime.utcnow()}
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                updates[key] = value

        mongo.db.tasks.update_one(
            {'_id': self._id, 'user_id': self.user_id},
            {'$set': updates}
        )
        
        # Invalidate caches
        redis_client.client.delete(f'tasks:{self.user_id}')
        redis_client.client.delete(f'task:{self._id}:{self.user_id}')

    def delete(self) -> None:
        """Delete task from database and update cache."""
        mongo.db.tasks.delete_one({'_id': self._id, 'user_id': self.user_id})
        
        # Invalidate caches
        redis_client.client.delete(f'tasks:{self.user_id}')
        redis_client.client.delete(f'task:{self._id}:{self.user_id}')