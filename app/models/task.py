from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import json
from bson import ObjectId
from marshmallow import Schema, fields, validate

from app.extensions import mongo, redis_client

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
        _id: Optional[ObjectId] = None
    ):
        self.title = title
        self.description = description
        self.user_id = user_id
        self.due_date = due_date
        self.status = status
        self._id = _id if _id else ObjectId()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert task object to dictionary."""
        return {
            'id': str(self._id),
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def save(self) -> 'Task':
        """Save the task to the database and invalidate cache."""
        task_data = {
            '_id': self._id,
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'due_date': self.due_date,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        mongo.db.tasks.insert_one(task_data)
        # Invalidate cache
        cache_key = f'tasks:{self.user_id}'
        redis_client.client.delete(cache_key)
        return self
    
    @classmethod
    def get_by_id(cls, task_id: str, user_id: str) -> Optional['Task']:
        """Get task by ID."""
        task_data = mongo.db.tasks.find_one({
            '_id': ObjectId(task_id),
            'user_id': user_id
        })
        return cls(**task_data) if task_data else None
    
    @classmethod
    def get_user_tasks(cls, user_id: str) -> List['Task']:
        """Get all tasks for a user with optional filtering and sorting."""
        # Try to get from cache first
        cache_key = f'tasks:{user_id}'
        cached_tasks = redis_client.client.get(cache_key)
        
        if cached_tasks:
            # Deserialize the cached tasks and convert back to Task objects
            tasks_data = json.loads(cached_tasks)
            tasks = []
            for task_data in tasks_data:
                task = cls(
                    title=task_data['title'],
                    description=task_data['description'],
                    user_id=task_data['user_id'],
                    status=task_data['status'],
                    _id=ObjectId(task_data['id'].replace('ObjectId(\'', '').replace('\')', ''))
                )
                if task_data.get('due_date'):
                    task.due_date = datetime.fromisoformat(task_data['due_date'].replace('Z', '+00:00'))
                task.created_at = datetime.fromisoformat(task_data['created_at'].replace('Z', '+00:00'))
                task.updated_at = datetime.fromisoformat(task_data['updated_at'].replace('Z', '+00:00'))
                tasks.append(task)
            return tasks

        # If not in cache, get from database
        tasks_data = mongo.db.tasks.find({'user_id': user_id})
        
        tasks = []
        for task_data in tasks_data:
            task = cls(
                title=task_data['title'],
                description=task_data['description'],
                status=task_data['status'],
                due_date=task_data['due_date'],
                user_id=task_data['user_id'],
                _id=task_data['_id']
            )
            task.created_at = task_data['created_at']
            task.updated_at = task_data['updated_at']
            tasks.append(task)
        
        # Cache the results for 5 minutes
        # Serialize tasks before storing in Redis
        serialized_tasks = json.dumps([task.to_dict() for task in tasks])
        redis_client.client.setex(
            cache_key,
            300,  # 5 minutes
            serialized_tasks
        )
        
        return tasks
    
    def update(self, **kwargs) -> 'Task':
        """Update task fields."""
        updates = {
            'updated_at': datetime.utcnow()
        }
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                updates[key] = value
        
        mongo.db.tasks.update_one(
            {'_id': self._id},
            {'$set': updates}
        )
        # Invalidate cache
        cache_key = f'tasks:{self.user_id}'
        redis_client.client.delete(cache_key)
        return self
    
    def delete(self) -> None:
        """Delete task."""
        mongo.db.tasks.delete_one({'_id': self._id})
        # Invalidate cache
        cache_key = f'tasks:{self.user_id}'
        redis_client.client.delete(cache_key) 