from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app import db
from app.models import Attendance, Workout, Member, User

admin_reports_bp = Blueprint('admin_reports', __name__)


def _require_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return None
    return user


@admin_reports_bp.route('/attendance-frequency', methods=['GET'])
@jwt_required()
def attendance_frequency():
    """
    Attendance frequency aggregation for last N days
    ---
    tags:
      - Admin Reports
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 30
      - name: top
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: Aggregated attendance frequencies
      401:
        description: Unauthorized
      403:
        description: Admin access required
    """
    if not _require_admin():
        return jsonify({'message': 'Admin access required'}), 403

    days = int(request.args.get('days', 30))
    top = int(request.args.get('top', 10))
    since = datetime.utcnow() - timedelta(days=days)

    # total checkins in range
    total_checkins = db.session.query(func.count(Attendance.id)).filter(Attendance.check_in_time >= since).scalar() or 0

    # per-member counts (paginated)
    members_query = db.session.query(
      Member.id.label('memberId'),
      Member.name.label('memberName'),
      func.count(Attendance.id).label('checkins')
    ).join(Attendance, Member.id == Attendance.member_id).filter(Attendance.check_in_time >= since).group_by(Member.id).order_by(func.count(Attendance.id).desc())

    total_members_with_activity = members_query.count()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', top))
    members_counts = members_query.limit(per_page).offset((page - 1) * per_page).all()

    avg_checkins = float(total_checkins) / (db.session.query(func.count(Member.id)).scalar() or 1)

    result = {
      'totalCheckins': int(total_checkins),
      'avgCheckinsPerMember': avg_checkins,
      'totalMembersWithActivity': total_members_with_activity,
      'page': page,
      'per_page': per_page,
      'topMembers': [{'memberId': m.memberId, 'memberName': m.memberName, 'checkins': int(m.checkins)} for m in members_counts]
    }

    # support CSV export of the topMembers
    if request.args.get('format') == 'csv':
      import csv, io
      if not result['topMembers']:
        return jsonify({'message': 'No data to export'}), 404
      output = io.StringIO()
      writer = csv.DictWriter(output, fieldnames=['memberId', 'memberName', 'checkins'])
      writer.writeheader()
      writer.writerows(result['topMembers'])
      return (output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=attendance-top-members.csv'})

    return jsonify(result)


@admin_reports_bp.route('/workouts-summary', methods=['GET'])
@jwt_required()
def workouts_summary():
    """
    Recent workouts summary
    ---
    tags:
      - Admin Reports
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 30
    responses:
      200:
        description: Workouts summary
    """
    if not _require_admin():
        return jsonify({'message': 'Admin access required'}), 403

    days = int(request.args.get('days', 30))
    since = datetime.utcnow() - timedelta(days=days)

    total_workouts = db.session.query(func.count(Workout.id)).filter(Workout.date >= since).scalar() or 0
    avg_duration = db.session.query(func.avg(Workout.duration)).filter(Workout.date >= since).scalar() or 0

    types_query = db.session.query(Workout.type, func.count(Workout.id).label('count')).filter(Workout.date >= since).group_by(Workout.type).order_by(func.count(Workout.id).desc())

    # pagination for types list
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    types = types_query.limit(per_page).offset((page - 1) * per_page).all()

    result = {
      'totalWorkouts': int(total_workouts),
      'avgDuration': float(avg_duration) if avg_duration else 0,
      'page': page,
      'per_page': per_page,
      'byType': [{'type': t[0], 'count': int(t.count)} for t in types]
    }

    if request.args.get('format') == 'csv':
      import csv, io
      if not result['byType']:
        return jsonify({'message': 'No data to export'}), 404
      output = io.StringIO()
      writer = csv.DictWriter(output, fieldnames=['type', 'count'])
      writer.writeheader()
      writer.writerows(result['byType'])
      return (output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=workouts-by-type.csv'})

    return jsonify(result)


@admin_reports_bp.route('/members-activity', methods=['GET'])
@jwt_required()
def members_activity():
    """
    Active vs inactive members within a period
    ---
    tags:
      - Admin Reports
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 30
    responses:
      200:
        description: Members activity summary
    """
    if not _require_admin():
        return jsonify({'message': 'Admin access required'}), 403

    days = int(request.args.get('days', 30))
    since = datetime.utcnow() - timedelta(days=days)

    total_members = db.session.query(func.count(Member.id)).scalar() or 0

    # members with attendance or workouts in range
    active_members_q = db.session.query(Member.id).outerjoin(Attendance, Member.id == Attendance.member_id).outerjoin(Workout, Member.id == Workout.member_id).filter((Attendance.check_in_time >= since) | (Workout.date >= since)).distinct()
    active_count = active_members_q.count()
    inactive_count = int(total_members) - int(active_count)

    return jsonify({
        'totalMembers': int(total_members),
        'activeMembers': int(active_count),
        'inactiveMembers': int(inactive_count)
    })
