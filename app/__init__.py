from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flasgger import Swagger

from app.config import config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name='default'):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Swagger configuration
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api-docs"
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Gym Flow API",
            "description": "API documentation for the Gym Flow application - A comprehensive gym management system",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
            }
        },
        "security": [{"Bearer": []}]
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.members import members_bp
    from app.routes.attendance import attendance_bp
    from app.routes.workouts import workouts_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(members_bp, url_prefix='/api/members')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(workouts_bp, url_prefix='/api/workouts')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    # Health check route
    @app.route('/api/health')
    def health_check():
        from datetime import datetime
        return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}

    # Create tables
    # Note: do not create tables automatically here. Tests and deployment
    # scripts should control database creation/migrations explicitly. This
    # avoids attempting to connect to the production database during test
    # setup where tests override the database URI.

    return app
