
from flask import Blueprint, request, jsonify
import jwt
import bcrypt
from config import db, JWT_SECRET, redis_client
from models.user import create_user, find_user_by_email, update_password
from utils.email_service import send_password_reset

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt())
    create_user(db, {"email": data['email'], "password": hashed})
    return jsonify({"msg": "User created"}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = find_user_by_email(db, data['email'])
    # ...existing code...
    if user and bcrypt.checkpw(data['password'].encode(), user['password']):
        token = jwt.encode({"email": user['email']}, JWT_SECRET, algorithm="HS256")
        redis_client.set(token, "valid", ex=300)
        return jsonify({"token": token}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@user_bp.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    redis_client.delete(token)
    return jsonify({"msg": "Logged out"}), 200

@user_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data['email']
    send_password_reset(email)
    return jsonify({"msg": "Reset email sent"}), 200

@user_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    # ...retrive token from email link...
    new_hashed = bcrypt.hashpw(data['new_password'].encode(), bcrypt.gensalt())
    update_password(db, data['email'], new_hashed)
    return jsonify({"msg": "Password changed"}), 200