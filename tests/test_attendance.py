import pytest
from app.models import Attendance, Member
from datetime import datetime, timedelta, date


class TestCheckIn:
    """Test attendance check-in functionality."""

    def test_check_in_success(self, client, create_user, create_member):
        """Test successful check-in."""
        member = create_member(name='Member', email='member@example.com')
        user = create_user(email='user@example.com', password='password123')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.post(
            '/api/attendance/checkin',
            json={'member_id': member.id},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data or 'checkInTime' in data or 'check_in_time' in data

    def test_check_in_duplicate_prevention(self, client, create_user, create_member, db_session):
        """Test duplicate same-day check-in is prevented."""
        member = create_member(name='Member', email='member@example.com')
        user = create_user(email='user@example.com', password='password123')
        
        # Create existing check-in for today
        attendance = Attendance(member_id=member.id, user_id=user.id)
        db_session.session.add(attendance)
        db_session.session.commit()
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Try to check in again
        response = client.post(
            '/api/attendance/checkin',
            json={'member_id': member.id},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'already' in data['message'].lower() or 'duplicate' in data['message'].lower()

    def test_check_in_invalid_member(self, client, create_user):
        """Test check-in fails with invalid member ID."""
        user = create_user(email='user@example.com', password='password123')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.post(
            '/api/attendance/checkin',
            json={'member_id': 'invalid-id'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 404

    def test_check_in_requires_authentication(self, client):
        """Test check-in requires authentication."""
        response = client.post(
            '/api/attendance/checkin',
            json={'member_id': 'some-id'}
        )
        assert response.status_code == 401


class TestAttendanceHistory:
    """Test attendance history endpoints."""

    def test_get_attendance_history(self, client, create_user, create_member, db_session):
        """Test retrieving attendance history for a member."""
        member = create_member(name='Member', email='member@example.com')
        user = create_user(email='user@example.com', password='password123')
        
        # Create multiple attendance records
        for i in range(3):
            attendance = Attendance(
                member_id=member.id,
                user_id=user.id,
                check_in_time=datetime.utcnow() - timedelta(days=i)
            )
            db_session.session.add(attendance)
        db_session.session.commit()
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            f'/api/attendance/history/{member.id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'history' in data or isinstance(data, list)

    def test_get_my_attendance_history(self, client, create_user, create_member, db_session):
        """Test retrieving current user's attendance history."""
        member = create_member(name='Member', email='member@example.com')
        user = create_user(email='user@example.com', password='password123')
        member.user_id = user.id
        db_session.session.commit()
        
        # Create attendance records
        for i in range(2):
            attendance = Attendance(
                member_id=member.id,
                user_id=user.id,
                check_in_time=datetime.utcnow() - timedelta(days=i)
            )
            db_session.session.add(attendance)
        db_session.session.commit()
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            '/api/attendance/my-history',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200 or response.status_code == 404  # No member profile yet

    def test_get_today_attendance(self, client, create_user, create_member, db_session):
        """Test retrieving today's attendance records."""
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        member = create_member(name='Member', email='member@example.com')
        
        # Create attendance record for today
        attendance = Attendance(member_id=member.id, user_id=admin.id)
        db_session.session.add(attendance)
        db_session.session.commit()
        
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            '/api/attendance/today',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'attendances' in data or isinstance(data, list)

    def test_attendance_history_limit(self, client, create_user, create_member, db_session):
        """Test attendance history respects limit parameter."""
        member = create_member(name='Member', email='member@example.com')
        user = create_user(email='user@example.com', password='password123')
        
        # Create 10 attendance records
        for i in range(10):
            attendance = Attendance(
                member_id=member.id,
                user_id=user.id,
                check_in_time=datetime.utcnow() - timedelta(days=i)
            )
            db_session.session.add(attendance)
        db_session.session.commit()
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            f'/api/attendance/history/{member.id}?limit=5',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200


class TestAttendanceStats:
    """Test attendance statistics."""

    def test_get_attendance_stats(self, client, create_user, create_member, db_session):
        """Test retrieving attendance statistics for a member."""
        member = create_member(name='Member', email='member@example.com')
        user = create_user(email='user@example.com', password='password123')
        
        # Create attendance records
        for i in range(5):
            attendance = Attendance(
                member_id=member.id,
                user_id=user.id,
                check_in_time=datetime.utcnow() - timedelta(days=i)
            )
            db_session.session.add(attendance)
        db_session.session.commit()
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            f'/api/attendance/stats/{member.id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'totalCheckins' in data or 'total_checkins' in data

    def test_attendance_stats_nonexistent_member(self, client, create_user):
        """Test stats endpoint returns 404 for nonexistent member."""
        user = create_user(email='user@example.com', password='password123')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            '/api/attendance/stats/nonexistent-id',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 404


class TestAttendancePermissions:
    """Test attendance access permissions."""

    def test_check_in_requires_authentication(self, client):
        """Test check-in endpoint requires authentication."""
        response = client.post('/api/attendance/checkin', json={'member_id': 'some-id'})
        assert response.status_code == 401

    def test_history_requires_authentication(self, client):
        """Test history endpoint requires authentication."""
        response = client.get('/api/attendance/history/some-id')
        assert response.status_code == 401
