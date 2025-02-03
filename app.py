from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from redis import Redis
import jwt
import datetime
from functools import wraps
from prometheus_flask_exporter import PrometheusMetrics
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
redis_client = Redis.from_url(os.getenv("REDIS_URL"))
metrics = PrometheusMetrics(app)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(" ")[1]
            if not redis_client.exists(token):
                return jsonify({'message': 'Token is invalid'}), 401
            data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    user = mongo.db.users.find_one({"email": data["email"]})
    
    if user and bcrypt.checkpw(data["password"].encode('utf-8'), user["password"]):
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=300)
        }, os.getenv("JWT_SECRET_KEY"))
        redis_client.setex(token, 300, str(user['_id']))
        return jsonify({"token": token})
    
    return jsonify({"message": "Invalid credentials"}), 401

@app.route("/tasks", methods=["GET", "POST"])
@token_required
def tasks():
    if request.method == "POST":
        data = request.get_json()
        task_id = mongo.db.tasks.insert_one({
            "title": data["title"],
            "description": data["description"],
            "status": data["status"],
            "due_date": data["due_date"],
            "user_id": data["user_id"]
        }).inserted_id
        return jsonify({"message": "Task created", "task_id": str(task_id)}), 201
    
    tasks = list(mongo.db.tasks.find())
    return jsonify({"tasks": tasks}), 200

@app.route("/metrics")
def metrics():
    return generate_metrics()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
