from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import jwt
from app.models.user import User
from app.extensions import redis_client, mail
from flask_mail import Message
import uuid
from functools import wraps
from bson import ObjectId
import json

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def generate_token(user: User) -> str:
    payload = {
        'sub': str(user._id),
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'whitelisted': user.whitelisted,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    # Store token in Redis whitelist
    redis_client.client.setex(
        f"token:{token}",
        86400,  # 1 day in seconds
        json.dumps({
            'user_id': str(user._id),
            'email': user.email,
            'role': user.role
        })
    )
    return token

def verify_token(token):
    try:
        # First check if token is in Redis whitelist
        token_data = redis_client.client.get(f"token:{token}")
        if not token_data:
            return None
            
        # Then verify JWT signature and expiration
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        # Clean up expired token from Redis
        redis_client.client.delete(f"token:{token}")
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    if not payload:
        return None
    
    return User.get_by_id(payload['sub'])

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Authentication required'}), 401
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.get_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(
        email=data['email'],
        password=data['password'],
        name=data.get('name')
    )
    user.save()
    
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.get_by_email(data['email'])
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = generate_token(user)
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        # Remove token from Redis whitelist
        redis_client.client.delete(f"token:{token}")
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/reset-password', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    user = User.get_by_email(data['email'])
    
    if not user:
        return jsonify({'message': 'If the email exists, a reset link will be sent'}), 200
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    redis_client.client.setex(
        f"reset:{reset_token}",
        300,  # 5 minutes
        user.email
    )
    
    # Send reset email
    reset_url = f"{request.host_url}auth/reset-password/{reset_token}"
    msg = Message(
        'Password Reset Request',
        recipients=[user.email],
        body=f'To reset your password, visit the following link: {reset_url}\n'
             f'This link will expire in 5 minutes.'
    )
    mail.send(msg)
    
    return jsonify({'message': 'If the email exists, a reset link will be sent'}), 200

@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    email = redis_client.client.get(f"reset:{token}")
    
    if not email:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    User.update_password(email.decode('utf-8'), data['new_password'])
    redis_client.client.delete(f"reset:{token}")
    
    return jsonify({'message': 'Password updated successfully'}) 

@auth_bp.route('/permissions/<user_id>', methods=['PATCH'])
@admin_required
def update_user_permissions(current_user, user_id):
    try:
        data = request.get_json()
        if not isinstance(data.get('role'), str) or not isinstance(data.get('whitelisted'), bool):
            return jsonify({'error': 'Invalid request data'}), 400
        
        target_user = User.get_by_id(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
            
        update_data = {
            'role': data['role'],
            'whitelisted': data['whitelisted']
        }
        
        if User.update_user(target_user._id, update_data):
            return jsonify({'message': 'User permissions updated successfully'})
        else:
            return jsonify({'error': 'Failed to update user permissions'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500