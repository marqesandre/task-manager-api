from flask_pymongo import PyMongo
from flask_mail import Mail
import redis
from flask import current_app

class RedisClient:
    def __init__(self):
        self._redis_client = None

    def init_app(self, app):
        self._redis_client = redis.from_url(app.config['REDIS_URL'])

    @property
    def client(self):
        if self._redis_client is None:
            self._redis_client = redis.from_url(current_app.config['REDIS_URL'])
        return self._redis_client

mongo = PyMongo()
redis_client = RedisClient()
mail = Mail() 