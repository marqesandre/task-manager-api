from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import jwt
from app.models.user import User
from app.extensions import redis_client, mail
from flask_mail import Message
import uuid

auth_bp = Blueprint('auth', __name__)

def generate_token(email):
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(minutes=5)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload['email']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

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
    
    token = generate_token(user.email)
    
    # Store token in Redis with 5 minutes expiration
    redis_client.client.setex(
        f"token:{token}",
        300,  # 5 minutes
        user.email
    )
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    if token:
        token = token.split(' ')[1]
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
    reset_url = f"{request.host_url}reset-password/{reset_token}"
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