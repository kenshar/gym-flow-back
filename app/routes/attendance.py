from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from app import db
from app.models import Attendance, Member, User
from app.middleware.auth import admin_required

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/checkin', methods=['POST'])
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
            - member_id
          properties:
            member_id:
              type: string
              example: "123e4567-e89b-12d3-a456-426614174000"
    responses:
      201:
        description: Check-in successful
        schema:
          type: object
          properties:
            message:
              type: string
              example: Check-in successful
            data:
              type: object
      400:
        description: Member ID required or already checked in today
      404:
        description: Member not found
    """
    data = request.get_json()
    member_id = data.get('member_id')
    user_id = get_jwt_identity()

    if not member_id:
        return jsonify({'message': 'member_id is required'}), 400

    # Check if member exists
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    # Check if member has active membership
    if member.membership_status not in ['active', 'premium', 'vip']:
        return jsonify({
            'message': f'Cannot check in. Membership status: {member.membership_status}'
        }), 400

    # Check for duplicate check-in today
    if Attendance.has_checked_in_today(member_id):
        return jsonify({'message': 'Already checked in today'}), 400

    # Create attendance record
    attendance = Attendance(
        member_id=member_id,
        user_id=user_id
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        'message': 'Check-in successful! 🎉',
        'data': attendance.to_dict()
    }), 201


@attendance_bp.route('/history/<member_id>', methods=['GET'])
@jwt_required()
def get_attendance_history(member_id):
    """
    Get attendance history for a member
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - in: path
        name: member_id
        type: string
        required: true
        description: Member ID
      - in: query
        name: limit
        type: integer
        default: 30
        description: Maximum number of records to return
    responses:
      200:
        description: Attendance history retrieved successfully
        schema:
          type: object
          properties:
            memberId:
              type: string
            totalCheckins:
              type: integer
            history:
              type: array
              items:
                type: object
      404:
        description: Member not found
    """
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    limit = request.args.get('limit', 30, type=int)
    records = Attendance.get_member_history(member_id, limit)

    return jsonify({
        'memberId': member_id,
        'memberName': member.name,
        'totalCheckins': len(records),
        'history': [record.to_dict() for record in records]
    })


@attendance_bp.route('/my-history', methods=['GET'])
@jwt_required()
def get_my_attendance():
    """
    Get attendance history for the current user
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - in: query
        name: limit
        type: integer
        default: 30
        description: Maximum number of records to return
    responses:
      200:
        description: User's attendance history
      404:
        description: No member profile found for this user
    """
    user_id = get_jwt_identity()
    
    # Find member associated with this user
    member = Member.query.filter_by(user_id=user_id).first()
    if not member:
        return jsonify({'message': 'No member profile found'}), 404

    limit = request.args.get('limit', 30, type=int)
    records = Attendance.get_member_history(member.id, limit)

    return jsonify({
        'memberId': member.id,
        'memberName': member.name,
        'totalCheckins': len(records),
        'history': [record.to_dict() for record in records]
    })


@attendance_bp.route('/today', methods=['GET'])
@admin_required
def get_today_attendance():
    """
    Get all check-ins for today (Admin only)
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    responses:
      200:
        description: Today's attendance list
        schema:
          type: object
          properties:
            date:
              type: string
            totalCheckins:
              type: integer
            attendances:
              type: array
              items:
                type: object
      403:
        description: Admin access required
    """
    attendances = Attendance.get_today_attendances()
    
    return jsonify({
        'date': date.today().isoformat(),
        'totalCheckins': len(attendances),
        'attendances': [attendance.to_dict() for attendance in attendances]
    })


@attendance_bp.route('/stats/<member_id>', methods=['GET'])
@jwt_required()
def get_attendance_stats(member_id):
    """
    Get attendance statistics for a member
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - in: path
        name: member_id
        type: string
        required: true
    responses:
      200:
        description: Attendance statistics
        schema:
          type: object
          properties:
            memberId:
              type: string
            totalCheckins:
              type: integer
            thisMonth:
              type: integer
            thisWeek:
              type: integer
            lastCheckIn:
              type: string
      404:
        description: Member not found
    """
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    # Get all attendance records
    all_records = Attendance.query.filter_by(member_id=member_id).all()
    
    # Calculate stats
    now = datetime.utcnow()
    this_month = now.month
    this_year = now.year
    
    month_count = sum(
        1 for r in all_records 
        if r.check_in_time.month == this_month and r.check_in_time.year == this_year
    )
    
    # This week (last 7 days)
    from datetime import timedelta
    one_week_ago = now - timedelta(days=7)
    week_count = sum(1 for r in all_records if r.check_in_time >= one_week_ago)
    
    # Last check-in
    last_record = Attendance.query.filter_by(
        member_id=member_id
    ).order_by(Attendance.check_in_time.desc()).first()
    
    return jsonify({
        'memberId': member_id,
        'memberName': member.name,
        'totalCheckins': len(all_records),
        'thisMonth': month_count,
        'thisWeek': week_count,
        'lastCheckIn': last_record.check_in_time.isoformat() if last_record else None
    })


@attendance_bp.route('/delete/<attendance_id>', methods=['DELETE'])
@admin_required
def delete_attendance(attendance_id):
    """
    Delete an attendance record (Admin only)
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - in: path
        name: attendance_id
        type: string
        required: true
    responses:
      200:
        description: Attendance record deleted
      403:
        description: Admin access required
      404:
        description: Attendance record not found
    """
    attendance = Attendance.query.get(attendance_id)
    if not attendance:
        return jsonify({'message': 'Attendance record not found'}), 404

    db.session.delete(attendance)
    db.session.commit()

    return jsonify({'message': 'Attendance record deleted successfully'})