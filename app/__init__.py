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

    # Configure CORS - allow frontend origins
    CORS(app, resources={r"/api/*": {
        "origins": ["https://kenshar.github.io", "http://localhost:5173", "http://localhost:3000"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "supports_credentials": True
    }})

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
    from app.routes.admin_reports import admin_reports_bp
    from app.routes.admin_invites import admin_invites_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(members_bp, url_prefix='/api/members')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(workouts_bp, url_prefix='/api/workouts')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(admin_reports_bp, url_prefix='/api/admin/reports')
    app.register_blueprint(admin_invites_bp, url_prefix='/api/admin/invites')

    # Root route
    @app.route('/')
    def index():
        return {
            'name': 'Gym Flow API',
            'version': '1.0.0',
            'status': 'running',
            'documentation': '/api-docs'
        }

    # Health check route
    @app.route('/api/health')
    def health_check():
        from datetime import datetime
        return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}

    # Create tables and seed data (non-blocking)
    try:
        with app.app_context():
            try:
                db.create_all()
                print("Database tables created successfully")
            except Exception as e:
                print(f"Database create error: {e}")

            # Seed admin user if not exists
            try:
                from app.models.user import User
                admin = User.query.filter_by(email='admin@example.com').first()
                if not admin:
                    admin = User(
                        name='Admin User',
                        email='admin@example.com',
                        role='admin'
                    )
                    admin.set_password('password123')
                    db.session.add(admin)
                    db.session.commit()
                    print("Admin user created: admin@example.com")
            except Exception as e:
                print(f"Seed error: {e}")
    except Exception as e:
        print(f"Database init skipped: {e}")

    return app
