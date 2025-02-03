from flask import Flask
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
from flask_mail import Mail

from app.config import Config
from app.extensions import mongo, redis_client, mail
from app.routes.auth import auth_bp
from app.routes.tasks import tasks_bp
from app.routes.metrics import metrics_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    PrometheusMetrics(app)
    mail.init_app(app)
    mongo.init_app(app)
    redis_client.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(metrics_bp, url_prefix='/api/metrics')

    return app 