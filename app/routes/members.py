from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from app import db
from app.models import Member, Attendance, Workout
from app.middleware import admin_required

members_bp = Blueprint('members', __name__)


@members_bp.route('', methods=['GET'])
@admin_required
def get_members():
    """
    Get all members with filtering and pagination
    ---
    tags:
      - Members
    security:
      - Bearer: []
    parameters:
      - name: search
        in: query
        type: string
        description: Search by name or email
      - name: status
        in: query
        type: string
        enum: [all, active, inactive, expired, suspended]
      - name: membershipType
        in: query
        type: string
        enum: [all, basic, premium, vip]
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
        description: List of members with pagination
      401:
        description: Unauthorized
      403:
        description: Admin access required
    """
    search = request.args.get('search')
    status = request.args.get('status')
    membership_type = request.args.get('membershipType')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))

    query = Member.query

    if search:
        query = query.filter(
            or_(
                Member.name.ilike(f'%{search}%'),
                Member.email.ilike(f'%{search}%')
            )
        )

    if status and status != 'all':
        query = query.filter(Member.membership_status == status)

    if membership_type and membership_type != 'all':
        query = query.filter(Member.membership_type == membership_type)

    query = query.order_by(Member.created_at.desc())

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'members': [m.to_dict() for m in pagination.items],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@members_bp.route('/<member_id>', methods=['GET'])
@jwt_required()
def get_member(member_id):
    """
    Get a single member by ID
    ---
    tags:
      - Members
    security:
      - Bearer: []
    parameters:
      - name: member_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Member details
      404:
        description: Member not found
    """
    member = Member.query.get(member_id)

    if not member:
        return jsonify({'message': 'Member not found'}), 404

    return jsonify(member.to_dict())


@members_bp.route('/<member_id>/stats', methods=['GET'])
@jwt_required()
def get_member_stats(member_id):
    """
    Get member statistics
    ---
    tags:
      - Members
    security:
      - Bearer: []
    parameters:
      - name: member_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Member statistics
      401:
        description: Unauthorized
    """
    attendance_count = Attendance.query.filter_by(member_id=member_id).count()
    workout_count = Workout.query.filter_by(member_id=member_id).count()

    recent_attendance = Attendance.query.filter_by(member_id=member_id)\
        .order_by(Attendance.check_in_time.desc()).limit(5).all()

    recent_workouts = Workout.query.filter_by(member_id=member_id)\
        .order_by(Workout.date.desc()).limit(5).all()

    attendance_with_duration = Attendance.query.filter(
        Attendance.member_id == member_id,
        Attendance.duration.isnot(None)
    ).all()

    avg_duration = 0
    if attendance_with_duration:
        avg_duration = sum(a.duration for a in attendance_with_duration) / len(attendance_with_duration)

    return jsonify({
        'totalVisits': attendance_count,
        'totalWorkouts': workout_count,
        'averageVisitDuration': round(avg_duration),
        'recentAttendance': [a.to_dict() for a in recent_attendance],
        'recentWorkouts': [w.to_dict() for w in recent_workouts]
    })


@members_bp.route('', methods=['POST'])
@admin_required
def create_member():
    """
    Create a new member
    ---
    tags:
      - Members
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
          properties:
            name:
              type: string
            email:
              type: string
            phone:
              type: string
            membershipType:
              type: string
              enum: [basic, premium, vip]
            membershipStatus:
              type: string
              enum: [active, inactive, expired, suspended]
    responses:
      201:
        description: Member created successfully
      401:
        description: Unauthorized
      403:
        description: Admin access required
    """
    data = request.get_json()

    member = Member(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        membership_type=data.get('membershipType', 'basic'),
        membership_status=data.get('membershipStatus', 'active'),
        membership_end_date=data.get('membershipEndDate'),
        emergency_contact_name=data.get('emergencyContactName'),
        emergency_contact_phone=data.get('emergencyContactPhone'),
        emergency_contact_relationship=data.get('emergencyContactRelationship'),
        notes=data.get('notes')
    )

    db.session.add(member)
    db.session.commit()

    return jsonify(member.to_dict()), 201


@members_bp.route('/<member_id>', methods=['PUT'])
@admin_required
def update_member(member_id):
    """
    Update a member
    ---
    tags:
      - Members
    security:
      - Bearer: []
    parameters:
      - name: member_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
            phone:
              type: string
            membershipType:
              type: string
            membershipStatus:
              type: string
    responses:
      200:
        description: Member updated successfully
      404:
        description: Member not found
    """
    member = Member.query.get(member_id)

    if not member:
        return jsonify({'message': 'Member not found'}), 404

    data = request.get_json()

    if 'name' in data:
        member.name = data['name']
    if 'email' in data:
        member.email = data['email']
    if 'phone' in data:
        member.phone = data['phone']
    if 'membershipType' in data:
        member.membership_type = data['membershipType']
    if 'membershipStatus' in data:
        member.membership_status = data['membershipStatus']
    if 'membershipEndDate' in data:
        member.membership_end_date = data['membershipEndDate']
    if 'emergencyContactName' in data:
        member.emergency_contact_name = data['emergencyContactName']
    if 'emergencyContactPhone' in data:
        member.emergency_contact_phone = data['emergencyContactPhone']
    if 'emergencyContactRelationship' in data:
        member.emergency_contact_relationship = data['emergencyContactRelationship']
    if 'notes' in data:
        member.notes = data['notes']

    db.session.commit()

    return jsonify(member.to_dict())


@members_bp.route('/<member_id>', methods=['DELETE'])
@admin_required
def delete_member(member_id):
    """
    Delete a member
    ---
    tags:
      - Members
    security:
      - Bearer: []
    parameters:
      - name: member_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Member deleted successfully
      404:
        description: Member not found
    """
    member = Member.query.get(member_id)

    if not member:
        return jsonify({'message': 'Member not found'}), 404

    db.session.delete(member)
    db.session.commit()

    return jsonify({'message': 'Member deleted successfully'})
