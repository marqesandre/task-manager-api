from datetime import datetime
import bcrypt
from bson import ObjectId
from typing import Optional, Dict
from flask import current_app
from app.extensions import mongo

class User:
    def __init__(self, email: str, password: str, name: Optional[str] = None, _id: Optional[ObjectId] = None, created_at: Optional[datetime] = None):
        self.email = email
        self.password = self._hash_password(password) if isinstance(password, str) else password
        self.name = name
        self._id = _id if _id else ObjectId()
        self.created_at = created_at if created_at else datetime.utcnow()

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
            'created_at': self.created_at.isoformat()
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
            'created_at': self.created_at
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