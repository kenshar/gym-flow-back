"""
Workouts Routes - Workout & Assignment Management
==================================================
Purpose: Create, assign, and track member workouts with statistics.

Implemented:
  Get workout types
  Create/Update/Delete workouts
  Assign/Unassign members to workouts
  Get user's workouts with filtering
  Get member's workouts
  Filter by type and date range
  Duration and activity tracking

Logic Flow - Dependencies & Branches:
  ← Receives from: User model (coach/staff)
  ← Receives from: Member model (participants)
  ← Receives from: auth middleware (JWT validation)
  → Sends data to: admin_reports.py (workout statistics)
  → Sends data to: reports.py (member activity history)
  → Queries: Attendance + Workouts for member analytics

Data Flow in System:
  User (coach) creates Workout 
  → Members assigned to Workout
  → Workout duration/type tracked
  → Data flows to admin_reports.py & reports.py
  → Combined with Attendance for member analytics
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Workout, User, Member

workouts_bp = Blueprint('workouts', __name__)


WORKOUT_TYPES = [
    {'name': 'Strength Training', 'icon': 'dumbbell'},
    {'name': 'Cardio', 'icon': 'heart'},
    {'name': 'HIIT', 'icon': 'fire'},
    {'name': 'Yoga', 'icon': 'spa'},
    {'name': 'Pilates', 'icon': 'accessibility'},
    {'name': 'Swimming', 'icon': 'pool'},
    {'name': 'CrossFit', 'icon': 'fitness'},
    {'name': 'Other', 'icon': 'more'},
]


@workouts_bp.route('/types', methods=['GET'])
@jwt_required()
def get_workout_types():
    """
    Get available workout types
    ---
    tags:
      - Workouts
    security:
      - Bearer: []
    responses:
      200:
        description: List of workout types
      401:
        description: Unauthorized
    """
    return jsonify(WORKOUT_TYPES)


@workouts_bp.route('', methods=['GET'])
@jwt_required()
def get_workouts():
    """
    Get user's workouts with filtering and pagination
    ---
    tags:
      - Workouts
    security:
      - Bearer: []
    parameters:
      - name: type
        in: query
        type: string
        enum: [Strength Training, Cardio, HIIT, Yoga, Pilates, Swimming, CrossFit, Other]
      - name: startDate
        in: query
        type: string
        format: date-time
      - name: endDate
        in: query
        type: string
        format: date-time
      - name: page
        in: query
        type: integer
        default: 1
      - name: limit
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: List of workouts with pagination
      401:
        description: Unauthorized
    """
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    is_admin = current_user and current_user.role == 'admin'

    workout_type = request.args.get('type')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    member_id = request.args.get('memberId')

    # Admins may specify `memberId` to view workouts for a member, otherwise regular users only see their own workouts
    if is_admin and member_id:
      query = Workout.query.filter(Workout.member_id == member_id)
    else:
      query = Workout.query.filter(Workout.user_id == user_id)

    if workout_type:
        query = query.filter(Workout.type == workout_type)

    if start_date:
        query = query.filter(Workout.date >= datetime.fromisoformat(start_date.replace('Z', '+00:00')))

    if end_date:
        query = query.filter(Workout.date <= datetime.fromisoformat(end_date.replace('Z', '+00:00')))

    query = query.order_by(Workout.date.desc())

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'workouts': [w.to_dict() for w in pagination.items],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@workouts_bp.route('/<workout_id>', methods=['GET'])
@jwt_required()
def get_workout(workout_id):
    """
    Get a single workout by ID
    ---
    tags:
      - Workouts
    security:
      - Bearer: []
    parameters:
      - name: workout_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Workout details
      404:
        description: Workout not found
    """
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    is_admin = current_user and current_user.role == 'admin'

    if is_admin:
      workout = Workout.query.filter_by(id=workout_id).first()
    else:
      workout = Workout.query.filter_by(id=workout_id, user_id=user_id).first()

    if not workout:
      return jsonify({'message': 'Workout not found'}), 404

    return jsonify(workout.to_dict())


@workouts_bp.route('', methods=['POST'])
@jwt_required()
def create_workout():
    """
    Create a new workout
    ---
    tags:
      - Workouts
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - type
            - duration
          properties:
            type:
              type: string
              enum: [Strength Training, Cardio, HIIT, Yoga, Pilates, Swimming, CrossFit, Other]
            name:
              type: string
            duration:
              type: integer
              minimum: 1
            calories:
              type: integer
            intensity:
              type: string
              enum: [low, medium, high]
            exercises:
              type: array
            notes:
              type: string
            date:
              type: string
              format: date-time
    responses:
      201:
        description: Workout created successfully
      400:
        description: Validation error
    """
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    is_admin = current_user and current_user.role == 'admin'

    data = request.get_json() or {}

    # basic validation
    wtype = data.get('type')
    duration = int(data.get('duration', 0))
    if not wtype:
      return jsonify({'message': 'Workout type is required'}), 400
    if duration < 1:
      return jsonify({'message': 'Duration must be at least 1 minute'}), 400

    # validate exercises
    exercises = data.get('exercises', []) or []
    for i, ex in enumerate(exercises):
      if not ex.get('name') or str(ex.get('name')).strip() == '':
        return jsonify({'message': f'Exercise #{i+1} is missing a name'}), 400
      if 'sets' in ex and ex.get('sets') != '' and (not str(ex.get('sets')).isdigit() or int(ex.get('sets')) < 1):
        return jsonify({'message': f'Exercise #{i+1} sets must be an integer >= 1'}), 400
      if 'reps' in ex and ex.get('reps') != '' and (not str(ex.get('reps')).isdigit() or int(ex.get('reps')) < 1):
        return jsonify({'message': f'Exercise #{i+1} reps must be an integer >= 1'}), 400
      if 'weight' in ex and ex.get('weight') != '':
        try:
          if float(ex.get('weight')) < 0:
            return jsonify({'message': f'Exercise #{i+1} weight must be >= 0'}), 400
        except Exception:
          return jsonify({'message': f'Exercise #{i+1} weight must be a number'}), 400

    # validate member ownership if provided
    member_id = data.get('memberId') or data.get('member_id')
    if member_id:
      member = Member.query.get(member_id)
      if not member:
        return jsonify({'message': 'Member not found'}), 404
      # if member has an owner (user_id) enforce ownership unless admin
      if member.user_id and member.user_id != user_id and not is_admin:
        return jsonify({'message': 'You are not allowed to link a workout to this member'}), 403

    workout_date = data.get('date')
    if workout_date:
      workout_date = datetime.fromisoformat(workout_date.replace('Z', '+00:00'))
    else:
      workout_date = datetime.utcnow()

    workout = Workout(
      user_id=user_id,
      member_id=member_id,
      type=wtype,
      name=data.get('name'),
      duration=duration,
      calories=int(data.get('calories', 0)),
      intensity=data.get('intensity', 'medium'),
      exercises=exercises,
      notes=data.get('notes'),
      date=workout_date
    )

    db.session.add(workout)
    db.session.commit()

    return jsonify(workout.to_dict()), 201


@workouts_bp.route('/<workout_id>', methods=['PUT'])
@jwt_required()
def update_workout(workout_id):
    """
    Update a workout
    ---
    tags:
      - Workouts
    security:
      - Bearer: []
    parameters:
      - name: workout_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            type:
              type: string
            name:
              type: string
            duration:
              type: integer
            calories:
              type: integer
            intensity:
              type: string
            exercises:
              type: array
            notes:
              type: string
            date:
              type: string
    responses:
      200:
        description: Workout updated successfully
      404:
        description: Workout not found
    """
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    is_admin = current_user and current_user.role == 'admin'

    if is_admin:
      workout = Workout.query.filter_by(id=workout_id).first()
    else:
      workout = Workout.query.filter_by(id=workout_id, user_id=user_id).first()

    if not workout:
      return jsonify({'message': 'Workout not found'}), 404

    data = request.get_json() or {}

    if 'type' in data:
        workout.type = data['type']
    if 'name' in data:
        workout.name = data['name']
    if 'duration' in data:
        workout.duration = int(data['duration'])
    if 'calories' in data:
        workout.calories = int(data['calories'])
    if 'intensity' in data:
        workout.intensity = data['intensity']
    if 'exercises' in data:
      # validate exercises similar to create
      exercises = data.get('exercises') or []
      for i, ex in enumerate(exercises):
        if not ex.get('name') or str(ex.get('name')).strip() == '':
          return jsonify({'message': f'Exercise #{i+1} is missing a name'}), 400
        if 'sets' in ex and ex.get('sets') != '' and (not str(ex.get('sets')).isdigit() or int(ex.get('sets')) < 1):
          return jsonify({'message': f'Exercise #{i+1} sets must be an integer >= 1'}), 400
        if 'reps' in ex and ex.get('reps') != '' and (not str(ex.get('reps')).isdigit() or int(ex.get('reps')) < 1):
          return jsonify({'message': f'Exercise #{i+1} reps must be an integer >= 1'}), 400
        if 'weight' in ex and ex.get('weight') != '':
          try:
            if float(ex.get('weight')) < 0:
              return jsonify({'message': f'Exercise #{i+1} weight must be >= 0'}), 400
          except Exception:
            return jsonify({'message': f'Exercise #{i+1} weight must be a number'}), 400
      workout.exercises = exercises
    if 'notes' in data:
        workout.notes = data['notes']
    if 'date' in data:
        workout.date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))

    # allow admins to change member association
    if 'memberId' in data or 'member_id' in data:
      member_id = data.get('memberId') or data.get('member_id')
      if member_id:
        member = Member.query.get(member_id)
        if not member:
          return jsonify({'message': 'Member not found'}), 404
        if member.user_id and member.user_id != user_id and not is_admin:
          return jsonify({'message': 'You are not allowed to link a workout to this member'}), 403
        workout.member_id = member_id
      else:
        workout.member_id = None

    db.session.commit()

    return jsonify(workout.to_dict())


@workouts_bp.route('/<workout_id>', methods=['DELETE'])
@jwt_required()
def delete_workout(workout_id):
    """
    Delete a workout
    ---
    tags:
      - Workouts
    security:
      - Bearer: []
    parameters:
      - name: workout_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Workout deleted successfully
      404:
        description: Workout not found
    """
    user_id = get_jwt_identity()

    workout = Workout.query.filter_by(id=workout_id, user_id=user_id).first()

    if not workout:
        return jsonify({'message': 'Workout not found'}), 404

    db.session.delete(workout)
    db.session.commit()

    return jsonify({'message': 'Workout deleted successfully'})
