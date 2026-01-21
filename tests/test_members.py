import pytest
from app.models import Member, User


class TestMemberCRUD:
    """Test member CRUD operations."""

    def test_get_members_as_admin(self, client, create_user, create_member):
        """Test admin can retrieve all members."""
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        create_member(name='Member 1')
        create_member(name='Member 2')
        
        # Login as admin
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            '/api/members',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'members' in data or isinstance(data, list)

    def test_get_members_as_user_forbidden(self, client, create_user):
        """Test regular user cannot retrieve all members."""
        user = create_user(email='user@example.com', password='password123', role='user')
        
        # Login as user
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            '/api/members',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 403

    def test_create_member_as_admin(self, client, create_user):
        """Test admin can create a new member."""
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        
        # Login as admin
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.post(
            '/api/members',
            json={
                'name': 'New Member',
                'email': 'newmember@example.com',
                'phone': '555-1234',
                'membershipType': 'basic'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'New Member'
        assert data['email'] == 'newmember@example.com'

    def test_create_member_duplicate_email(self, client, create_user, create_member):
        """Test cannot create member with duplicate email."""
        create_member(email='existing@example.com')
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.post(
            '/api/members',
            json={
                'name': 'Another Member',
                'email': 'existing@example.com',
                'membershipType': 'basic'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 400

    def test_get_member_details(self, client, create_user, create_member):
        """Test retrieving individual member details."""
        member = create_member(name='Test Member', email='member@example.com')
        user = create_user(email='user@example.com', password='password123')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            f'/api/members/{member.id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Test Member'
        assert data['email'] == 'member@example.com'

    def test_update_member(self, client, create_user, create_member):
        """Test updating member information."""
        member = create_member(name='Old Name', email='member@example.com')
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.put(
            f'/api/members/{member.id}',
            json={
                'name': 'New Name',
                'phone': '555-9999'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'New Name'

    def test_delete_member(self, client, create_user, create_member):
        """Test deleting a member."""
        member = create_member(name='To Delete', email='delete@example.com')
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.delete(
            f'/api/members/{member.id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200

    def test_get_member_stats(self, client, create_user, create_member):
        """Test retrieving member statistics."""
        member = create_member(name='Test Member', email='member@example.com')
        user = create_user(email='user@example.com', password='password123')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        response = client.get(
            f'/api/members/{member.id}/stats',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'attendanceCount' in data or 'total_attendance' in data or 'totalAttendance' in data


class TestMembershipStatus:
    """Test membership status and validation."""

    def test_membership_status_values(self, client, create_user):
        """Test valid membership statuses."""
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        statuses = ['active', 'inactive', 'expired', 'suspended']
        
        for status in statuses:
            response = client.post(
                '/api/members',
                json={
                    'name': f'Member {status}',
                    'email': f'member-{status}@example.com',
                    'membershipStatus': status,
                    'membershipType': 'basic'
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            assert response.status_code == 201

    def test_membership_types(self, client, create_user):
        """Test valid membership types."""
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        types = ['basic', 'premium', 'vip']
        
        for idx, mtype in enumerate(types):
            response = client.post(
                '/api/members',
                json={
                    'name': f'Member {mtype}',
                    'email': f'member-{mtype}-{idx}@example.com',
                    'membershipType': mtype
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            assert response.status_code == 201
