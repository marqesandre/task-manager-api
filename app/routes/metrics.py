from flask import Blueprint, jsonify
from app.extensions import mongo, redis_client
from datetime import datetime, timedelta

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('', methods=['GET'])
def get_metrics():
    # Get total users
    total_users = mongo.db.users.count_documents({})
    
    # Get total tasks
    total_tasks = mongo.db.tasks.count_documents({})
    
    # Get tasks by status
    tasks_by_status = list(mongo.db.tasks.aggregate([
        {
            '$group': {
                '_id': '$status',
                'count': {'$sum': 1}
            }
        }
    ]))
    
    # Get tasks due today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    tasks_due_today = mongo.db.tasks.count_documents({
        'due_date': {'$gte': today, '$lt': tomorrow}
    })
    
    # Get active sessions (count of valid tokens in Redis)
    active_sessions = len([
        key for key in redis_client.client.keys('token:*')
        if redis_client.client.ttl(key) > 0
    ])
    
    return jsonify({
        'total_users': total_users,
        'total_tasks': total_tasks,
        'tasks_by_status': {
            item['_id']: item['count']
            for item in tasks_by_status
        },
        'tasks_due_today': tasks_due_today,
        'active_sessions': active_sessions,
        'timestamp': datetime.utcnow().isoformat()
    }) 