from flask import Blueprint, request, jsonify
import jwt
from config import db, JWT_SECRET, redis_client
from models.task import create_task, get_tasks, update_task, delete_task
from bson import ObjectId

task_bp = Blueprint('task_bp', __name__)

def token_required(f):
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not redis_client.get(token):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    decorated_function.__doc__ = f.__doc__
    return decorated_function

@task_bp.route('/', methods=['GET'])
@token_required
def list_tasks():
    user_email = jwt.decode(request.headers.get('Authorization'), JWT_SECRET, algorithms=["HS256"])['email']
    tasks = get_tasks(db, user_email)
    return jsonify(tasks)

@task_bp.route('/', methods=['POST'])
@token_required
def create_new_task():
    data = request.get_json()
    user_email = jwt.decode(request.headers.get('Authorization'), JWT_SECRET, algorithms=["HS256"])['email']
    data['user_id'] = user_email
    create_task(db, data)
    return jsonify({"msg": "Task created"}), 201

@task_bp.route('/<task_id>', methods=['PUT'])
@token_required
def update_existing_task(task_id):
    updates = request.get_json()
    update_task(db, ObjectId(task_id), updates)
    return jsonify({"msg": "Task updated"})

@task_bp.route('/<task_id>', methods=['DELETE'])
@token_required
def remove_task(task_id):
    delete_task(db, ObjectId(task_id))
    return jsonify({"msg": "Task deleted"})