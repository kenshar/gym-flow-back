import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flasgger import swag_from
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - password
          properties:
            name:
              type: string
              example: John Doe
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: password123
            phone:
              type: string
              example: "+1234567890"
    responses:
      201:
        description: User registered successfully
      400:
        description: Email already registered
    """
    data = request.get_json()

    # Check if user exists
    existing_user = User.query.filter_by(email=data.get('email')).first()
    if existing_user:
        return jsonify({'message': 'Email already registered'}), 400

    # Create new user
    user = User(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone')
    )
    user.set_password(data.get('password'))

    db.session.add(user)
    db.session.commit()

    # Generate token
    token = create_access_token(identity=user.id)

    return jsonify({
        'access_token': token,  # Changed from 'token'
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful
      400:
        description: Email and password are required
      401:
        description: Invalid email or password
    """
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid email or password'}), 401

    token = create_access_token(identity=user.id)

    return jsonify({
        'access_token': token,  # Changed from 'token'
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    })


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Current user information
      401:
        description: Unauthorized
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role
    })


@auth_bp.route('/reset-password', methods=['POST'])
def request_password_reset():
    """
    Request password reset
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              example: john@example.com
    responses:
      200:
        description: Password reset instructions sent
      404:
        description: User not found
    """
    data = request.get_json()
    email = data.get('email')

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Generate reset token
    reset_token = secrets.token_hex(32)
    user.reset_password_token = hashlib.sha256(reset_token.encode()).hexdigest()
    user.reset_password_expires = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()

    # In production, send email with reset link
    return jsonify({
        'message': 'Password reset instructions sent',
        'resetToken': reset_token
    })


@auth_bp.route('/reset-password/confirm', methods=['POST'])
def confirm_password_reset():
    """
    Confirm password reset
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - token
            - password
          properties:
            token:
              type: string
            password:
              type: string
              example: newpassword123
    responses:
      200:
        description: Password reset successful
      400:
        description: Invalid or expired reset token
    """
    data = request.get_json()
    token = data.get('token')
    password = data.get('password')

    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    user = User.query.filter_by(reset_password_token=hashed_token).first()

    if not user or user.reset_password_expires < datetime.utcnow():
        return jsonify({'message': 'Invalid or expired reset token'}), 400

    user.set_password(password)
    user.reset_password_token = None
    user.reset_password_expires = None
    db.session.commit()

    return jsonify({'message': 'Password reset successful'})