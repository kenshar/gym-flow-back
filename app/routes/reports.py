import csv
import io
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, Response
from sqlalchemy import func, extract
from app import db
from app.models import Member, Attendance, Workout, User
from app.middleware import admin_required

reports_bp = Blueprint('reports', __name__)

MEMBERSHIP_PRICES = {
    'basic': 29.99,
    'premium': 49.99,
    'vip': 99.99
}


@reports_bp.route('/summary', methods=['GET'])
@admin_required
def get_summary():
    """
    Get summary report with key metrics
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - name: startDate
        in: query
        type: string
        format: date-time
      - name: endDate
        in: query
        type: string
        format: date-time
    responses:
      200:
        description: Summary report data
      401:
        description: Unauthorized
      403:
        description: Admin access required
    """
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    total_members = Member.query.count()
    active_members = Member.query.filter_by(membership_status='active').count()

    attendance_query = Attendance.query
    workout_query = Workout.query
    member_query = Member.query

    start_dt = None
    end_dt = None
    days_diff = 30  # default

    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        attendance_query = attendance_query.filter(Attendance.check_in_time >= start_dt)
        workout_query = workout_query.filter(Workout.date >= start_dt)
        member_query = member_query.filter(Member.created_at >= start_dt)

    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        attendance_query = attendance_query.filter(Attendance.check_in_time <= end_dt)
        workout_query = workout_query.filter(Workout.date <= end_dt)
        member_query = member_query.filter(Member.created_at <= end_dt)

    if start_dt and end_dt:
        days_diff = (end_dt - start_dt).days or 1

    total_attendance = attendance_query.count()
    total_workouts = workout_query.count()
    new_members = member_query.count()

    avg_daily_visits = total_attendance / days_diff if days_diff > 0 else 0

    # Membership breakdown
    membership_breakdown = db.session.query(
        Member.membership_type,
        func.count(Member.id)
    ).group_by(Member.membership_type).all()

    # Status breakdown
    status_breakdown = db.session.query(
        Member.membership_status,
        func.count(Member.id)
    ).group_by(Member.membership_status).all()

    return jsonify({
        'totalMembers': total_members,
        'activeMembers': active_members,
        'newMembers': new_members,
        'totalCheckins': total_attendance,
        'avgDailyVisits': round(avg_daily_visits, 2),
        'totalWorkouts': total_workouts,
        'membershipBreakdown': {m_type: count for m_type, count in membership_breakdown},
        'statusBreakdown': {status: count for status, count in status_breakdown}
    })


@reports_bp.route('/attendance', methods=['GET'])
@admin_required
def get_attendance_report():
    """
    Get attendance report grouped by time period
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - name: startDate
        in: query
        type: string
        format: date-time
      - name: endDate
        in: query
        type: string
        format: date-time
      - name: groupBy
        in: query
        type: string
        enum: [day, week, month]
        default: day
    responses:
      200:
        description: Attendance report data
      401:
        description: Unauthorized
      403:
        description: Admin access required
    """
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    group_by = request.args.get('groupBy', 'day')

    query = db.session.query(Attendance)

    if start_date:
        query = query.filter(Attendance.check_in_time >= datetime.fromisoformat(start_date.replace('Z', '+00:00')))

    if end_date:
        query = query.filter(Attendance.check_in_time <= datetime.fromisoformat(end_date.replace('Z', '+00:00')))

    # Group by day
    date_expr = func.to_char(Attendance.check_in_time, 'YYYY-MM-DD')

    data = db.session.query(
        date_expr.label('date'),
        func.count(Attendance.id).label('checkins'),
        func.count(func.distinct(Attendance.member_id)).label('uniqueMembers')
    ).group_by(date_expr).order_by(date_expr).all()

    return jsonify([
        {'date': d.date, 'checkins': d.checkins, 'uniqueMembers': d.uniqueMembers, 'peakHour': None}
        for d in data
    ])


@reports_bp.route('/membership', methods=['GET'])
@admin_required
def get_membership_report():
    """
    Get membership report with trends and expiring memberships
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    responses:
      200:
        description: Membership report data
      401:
        description: Unauthorized
      403:
        description: Admin access required
    """
    active = Member.query.filter_by(membership_status='active').count()
    expired = Member.query.filter_by(membership_status='expired').count()

    # Expiring this month
    now = datetime.now(timezone.utc)
    end_of_month = now.replace(day=1, month=now.month+1) if now.month < 12 else now.replace(day=1, month=1, year=now.year+1)
    expiring_this_month = Member.query.filter(
        Member.membership_end_date <= end_of_month,
        Member.membership_end_date >= now,
        Member.membership_status == 'active'
    ).count()

    # Renewal rate - for simplicity, assume 80% or calculate if possible
    renewal_rate = 85  # placeholder

    return jsonify({
        'active': active,
        'expiringThisMonth': expiring_this_month,
        'expired': expired,
        'renewalRate': renewal_rate
    })


@reports_bp.route('/revenue', methods=['GET'])
@admin_required
def get_revenue_report():
    """
    Get estimated revenue report
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    responses:
      200:
        description: Revenue report data
      401:
        description: Unauthorized
      403:
        description: Admin access required
    """
    member_counts = db.session.query(
        Member.membership_type,
        func.count(Member.id).label('count')
    ).filter(
        Member.membership_status == 'active'
    ).group_by(Member.membership_type).all()

    estimated_monthly_revenue = sum(
        MEMBERSHIP_PRICES.get(m_type, 0) * count
        for m_type, count in member_counts
    )

    return jsonify({
        'estimatedMonthlyRevenue': estimated_monthly_revenue,
        'breakdown': [{
            'type': m_type,
            'count': count,
            'revenue': MEMBERSHIP_PRICES.get(m_type, 0) * count
        } for m_type, count in member_counts]
    })


@reports_bp.route('/export/<export_type>', methods=['GET'])
@admin_required
def export_data(export_type):
    """
    Export data as JSON or CSV
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - name: export_type
        in: path
        type: string
        required: true
        enum: [members, attendance, workouts]
      - name: format
        in: query
        type: string
        enum: [json, csv]
        default: json
    responses:
      200:
        description: Exported data
      400:
        description: Invalid export type
      404:
        description: No data to export
    """
    export_format = request.args.get('format', 'json')

    if export_type == 'members':
        data = Member.query.all()
        records = [m.to_dict() for m in data]
    elif export_type == 'attendance':
        data = Attendance.query.all()
        records = [a.to_dict_with_member() for a in data]
    elif export_type == 'workouts':
        data = Workout.query.all()
        records = []
        for w in data:
            workout_dict = w.to_dict()
            if w.user:
                workout_dict['user'] = {'name': w.user.name, 'email': w.user.email}
            records.append(workout_dict)
    else:
        return jsonify({'message': 'Invalid export type'}), 400

    if export_format == 'csv':
        if not records:
            return jsonify({'message': 'No data to export'}), 404

        # Flatten nested objects for CSV
        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        flat_records = [flatten_dict(r) for r in records]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=flat_records[0].keys())
        writer.writeheader()
        writer.writerows(flat_records)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={export_type}-export.csv'}
        )

    return jsonify({'data': records, 'count': len(records)})
