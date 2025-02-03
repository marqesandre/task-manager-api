from flask import Flask, jsonify
from flasgger import Swagger
from routes.user_routes import user_bp
from routes.task_routes import task_bp

app = Flask(__name__)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}
Swagger(app, config=swagger_config)

app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(task_bp, url_prefix='/tasks')

@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Metrics endpoint returning API health.
    ---
    responses:
      200:
        description: API is healthy
        examples:
          application/json: {"status": "ok"}
    """
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)