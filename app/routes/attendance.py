from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Attendance, Member

attendance_bp = Blueprint('attendance', __name__)


def get_start_of_day():
    """Get start of current day."""
    now = datetime.utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def get_end_of_day():
    """Get end of current day."""
    now = datetime.utcnow()
    return now.replace(hour=23, minute=59, second=59, microsecond=999999)


@attendance_bp.route('', methods=['GET'])
@jwt_required()
def get_attendance():
    """
    Get attendance records with filtering and pagination
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - name: memberId
        in: query
        type: string
        description: Filter by member ID
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
        description: List of attendance records with pagination
      401:
        description: Unauthorized
    """
    member_id = request.args.get('memberId')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))

    query = Attendance.query

    if member_id:
        query = query.filter(Attendance.member_id == member_id)

    if start_date:
        query = query.filter(Attendance.check_in_time >= datetime.fromisoformat(start_date.replace('Z', '+00:00')))

    if end_date:
        query = query.filter(Attendance.check_in_time <= datetime.fromisoformat(end_date.replace('Z', '+00:00')))

    query = query.order_by(Attendance.check_in_time.desc())

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'records': [a.to_dict_with_member() for a in pagination.items],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@attendance_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_attendance():
    """
    Get today's attendance records
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    responses:
      200:
        description: List of today's attendance records
      401:
        description: Unauthorized
    """
    start_of_day = get_start_of_day()
    end_of_day = get_end_of_day()

    records = Attendance.query.filter(
        Attendance.check_in_time.between(start_of_day, end_of_day)
    ).order_by(Attendance.check_in_time.desc()).all()

    return jsonify([a.to_dict_with_member() for a in records])


@attendance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_attendance_stats():
    """
    Get attendance statistics
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    responses:
      200:
        description: Attendance statistics
      401:
        description: Unauthorized
    """
    start_of_day = get_start_of_day()

    start_of_week = datetime.utcnow()
    start_of_week = start_of_week - timedelta(days=start_of_week.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    today_count = Attendance.query.filter(Attendance.check_in_time >= start_of_day).count()
    week_count = Attendance.query.filter(Attendance.check_in_time >= start_of_week).count()
    month_count = Attendance.query.filter(Attendance.check_in_time >= start_of_month).count()

    currently_checked_in = Attendance.query.filter(
        Attendance.check_in_time >= start_of_day,
        Attendance.check_out_time.is_(None)
    ).count()

    return jsonify({
        'today': today_count,
        'thisWeek': week_count,
        'thisMonth': month_count,
        'currentlyCheckedIn': currently_checked_in
    })


@attendance_bp.route('/check-in', methods=['POST'])
@jwt_required()
def check_in():
    """
    Check in a member
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - memberId
          properties:
            memberId:
              type: string
            notes:
              type: string
    responses:
      201:
        description: Check-in successful
      400:
        description: Member already checked in or membership not active
      404:
        description: Member not found
    """
    data = request.get_json()
    member_id = data.get('memberId')
    notes = data.get('notes')

    user_id = get_jwt_identity()

    # Verify member exists and is active
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    if member.membership_status != 'active':
        return jsonify({'message': 'Member membership is not active'}), 400

    # Check if already checked in today
    start_of_day = get_start_of_day()

    existing_check_in = Attendance.query.filter(
        Attendance.member_id == member_id,
        Attendance.check_in_time >= start_of_day,
        Attendance.check_out_time.is_(None)
    ).first()

    if existing_check_in:
        return jsonify({'message': 'Member is already checked in'}), 400

    attendance = Attendance(
        member_id=member_id,
        user_id=user_id,
        notes=notes
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify(attendance.to_dict()), 201


@attendance_bp.route('/check-out', methods=['POST'])
@jwt_required()
def check_out():
    """
    Check out a member
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - memberId
          properties:
            memberId:
              type: string
    responses:
      200:
        description: Check-out successful
      404:
        description: No active check-in found for today
    """
    data = request.get_json()
    member_id = data.get('memberId')

    start_of_day = get_start_of_day()

    attendance = Attendance.query.filter(
        Attendance.member_id == member_id,
        Attendance.check_in_time >= start_of_day,
        Attendance.check_out_time.is_(None)
    ).first()

    if not attendance:
        return jsonify({'message': 'No active check-in found for today'}), 404

    attendance.check_out_time = datetime.utcnow()
    attendance.calculate_duration()
    db.session.commit()

    return jsonify(attendance.to_dict())
