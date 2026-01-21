import json
from datetime import datetime, timedelta
from app import db
from app.models import Attendance, Workout


def auth_headers(client, email, password):
    resp = client.post('/api/auth/register', json={'name': 'T', 'email': email, 'password': password})
    assert resp.status_code == 201
    token = resp.get_json().get('access_token')
    return {'Authorization': f'Bearer {token}'}


def test_admin_endpoints_require_jwt(client):
    # no token -> 401
    resp = client.get('/api/admin/reports/attendance-frequency')
    assert resp.status_code == 401


def test_admin_blocked_for_non_admin(client, create_user):
    # create normal user and get token
    headers = auth_headers(client, 'normal@example.com', 'password')
    resp = client.get('/api/admin/reports/attendance-frequency', headers=headers)
    assert resp.status_code == 403


def test_reports_aggregations(client, create_user, create_member, db_session):
    # create admin and get headers
    admin = create_user(email='adminr@example.com', name='AdminR', role='admin')
    resp = client.post('/api/auth/login', json={'email': 'adminr@example.com', 'password': 'password'})
    token = resp.get_json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # create members and activity
    member1 = create_member(name='M1', email='m1@example.com')
    member2 = create_member(name='M2', email='m2@example.com')

    # create attendances for member1
    now = datetime.utcnow()
    a1 = Attendance(member_id=member1.id, user_id=None, check_in_time=now - timedelta(days=1))
    a2 = Attendance(member_id=member1.id, user_id=None, check_in_time=now - timedelta(days=2))
    db_session.session.add(a1)
    db_session.session.add(a2)

    # create workout for member2
    w1 = Workout(user_id=admin.id, member_id=member2.id, type='Cardio', duration=30, date=now - timedelta(days=3))
    db_session.session.add(w1)
    db_session.session.commit()

    # attendance-frequency
    resp = client.get('/api/admin/reports/attendance-frequency?days=7&top=5', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'totalCheckins' in data
    assert data['totalCheckins'] >= 2

    # CSV export of top members
    resp = client.get('/api/admin/reports/attendance-frequency?days=7&top=5&format=csv', headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type') == 'text/csv'
    body = resp.data.decode('utf-8')
    assert 'memberId' in body and '\n' in body

    # workouts-summary
    resp = client.get('/api/admin/reports/workouts-summary?days=7', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'totalWorkouts' in data

    # members-activity
    resp = client.get('/api/admin/reports/members-activity?days=7', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'activeMembers' in data and 'inactiveMembers' in data
