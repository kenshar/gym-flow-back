from flask import Blueprint, jsonify, render_template_string, current_app
from app import db
from app.models import User, Member, Workout, Attendance

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    """Simple landing page for developers/testing."""
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>Gym Flow - Home</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 2rem; }
          a { color: #0b5fff; }
        </style>
      </head>
      <body>
        <h1>Gym Flow</h1>
        <p>A lightweight developer landing page for the Gym Flow API.</p>
        <ul>
          <li><a href="/api/info">API Info (JSON)</a></li>
          <li><a href="/api-docs">Swagger UI</a></li>
          <li><a href="/api/health">Health Check</a></li>
        </ul>
      </body>
    </html>
    """
    return render_template_string(html)


@home_bp.route('/api/info')
def api_info():
    """Return basic API information and lightweight stats.

    This endpoint is safe for unauthenticated access and is intended
    for quick testing and integrations.
    """
    info = {
        'name': 'Gym Flow API',
        'version': '1.0.0',
        'docs': '/api-docs',
    }

    # Attempt to gather lightweight counts; if DB not available return None
    try:
        users_count = db.session.query(User).count()
    except Exception:
        users_count = None

    try:
        members_count = db.session.query(Member).count()
    except Exception:
        members_count = None

    try:
        workouts_count = db.session.query(Workout).count()
    except Exception:
        workouts_count = None

    try:
        attendance_count = db.session.query(Attendance).count()
    except Exception:
        attendance_count = None

    info['counts'] = {
        'users': users_count,
        'members': members_count,
        'workouts': workouts_count,
        'attendance': attendance_count,
    }

    return jsonify(info)
