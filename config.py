
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import redis

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
REDIS_HOST = os.getenv("REDIS_HOST")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client.get_database("taskmanager")

redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0)