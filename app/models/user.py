from datetime import datetime
import bcrypt
from bson import ObjectId
from typing import Optional, Dict
from flask import current_app
from app.extensions import mongo

class User:
    def __init__(self, email: str, password: str, name: Optional[str] = None, _id: Optional[ObjectId] = None, 
                 created_at: Optional[datetime] = None, role: str = 'user', whitelisted: bool = False):
        self.email = email
        self.password = self._hash_password(password) if isinstance(password, str) else password
        self.name = name
        self._id = _id if _id else ObjectId()
        self.created_at = created_at if created_at else datetime.utcnow()
        self.role = role
        self.whitelisted = whitelisted

    @staticmethod
    def _hash_password(password: str) -> bytes:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

    def to_dict(self) -> Dict:
        return {
            'id': str(self._id),
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'role': self.role,
            'whitelisted': self.whitelisted
        }

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        user_data = mongo.db.users.find_one({'email': email})
        if not user_data:
            return None
        # Convert ObjectId to string in the id field
        user_data['_id'] = user_data.get('_id')
        return cls(**user_data)

    def save(self) -> 'User':
        user_data = {
            '_id': self._id,
            'email': self.email,
            'password': self.password,
            'name': self.name,
            'created_at': self.created_at,
            'role': self.role,
            'whitelisted': self.whitelisted
        }
        mongo.db.users.insert_one(user_data)
        return self

    @staticmethod
    def update_password(email: str, new_password: str) -> None:
        hashed_password = User._hash_password(new_password)
        mongo.db.users.update_one(
            {'email': email},
            {'$set': {'password': hashed_password}}
        ) 

    @staticmethod
    def update_user(user_id: ObjectId, update_data: Dict) -> bool:
        result = mongo.db.users.update_one(
            {'_id': user_id},
            {'$set': update_data}
        )
        return result.modified_count > 0

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional['User']:
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if not user_data:
                return None
            return cls(**user_data)
        except:
            return None