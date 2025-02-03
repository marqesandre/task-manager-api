import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # MongoDB
    MONGO_URI = os.getenv('MONGODB_URI')

    # Redis
    REDIS_URL = os.getenv('REDIS_URI')

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 300))  # 5 minutes
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') 