from flask import Blueprint, request, jsonify, g
from functools import wraps
from app.models.task import Task
from app.extensions import redis_client
from datetime import datetime
from bson import ObjectId

tasks_bp = Blueprint('tasks', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        token = token.split(' ')[1]
        email = redis_client.client.get(f"token:{token}")
        
        if not email:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        g.user_email = email.decode('utf-8')
        return f(*args, **kwargs)
    return decorated_function

def parse_iso_date(date_str: str) -> datetime:
    """Parse ISO 8601 date string to datetime object."""
    try:
        # Remove the 'Z' and replace with '+00:00' for UTC
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None

@tasks_bp.route('', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    
    # Convert string date to datetime if provided
    due_date = None
    if data.get('due_date'):
        due_date = parse_iso_date(data['due_date'])
        if due_date is None:
            return jsonify({'error': 'Invalid date format. Use ISO 8601 format (e.g., 2024-12-31T23:59:59Z)'}), 400
    
    task = Task(
        title=data['title'],
        description=data['description'],
        user_id=g.user_email,
        due_date=due_date,
        status=data.get('status', 'pending')
    )
    task.save()
    
    return jsonify(task.to_dict()), 201

@tasks_bp.route('', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.get_user_tasks(g.user_email)
    return jsonify([task.to_dict() for task in tasks])

@tasks_bp.route('/<task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    task = Task.get_by_id(task_id, g.user_email)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(task.to_dict())

@tasks_bp.route('/<task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.get_by_id(task_id, g.user_email)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    updates = {}
    
    if 'title' in data:
        updates['title'] = data['title']
    if 'description' in data:
        updates['description'] = data['description']
    if 'status' in data:
        updates['status'] = data['status']
    if 'due_date' in data:
        updates['due_date'] = parse_iso_date(data['due_date']) if data['due_date'] else None
    
    task.update(**updates)
    return jsonify(task.to_dict())

@tasks_bp.route('/<task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.get_by_id(task_id, g.user_email)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    task.delete()
    return jsonify({'message': 'Task deleted successfully'}) 