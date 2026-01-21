import pytest
from app.models import User


class TestAuthRegistration:
    """Test user registration endpoints."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post('/api/auth/register', json={
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'User registered successfully'
        assert 'user' in data

    def test_register_duplicate_email(self, client, create_user):
        """Test registration fails with duplicate email."""
        create_user(email='duplicate@example.com')
        response = client.post('/api/auth/register', json={
            'name': 'Another User',
            'email': 'duplicate@example.com',
            'password': 'password123'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'already exists' in data['message'].lower()

    def test_register_missing_fields(self, client):
        """Test registration fails with missing fields."""
        response = client.post('/api/auth/register', json={
            'name': 'John Doe'
            # Missing email and password
        })
        assert response.status_code == 400


class TestAuthLogin:
    """Test user login endpoints."""

    def test_login_success(self, client, create_user):
        """Test successful login."""
        create_user(email='user@example.com', password='password123')
        response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['email'] == 'user@example.com'

    def test_login_invalid_email(self, client):
        """Test login fails with invalid email."""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert 'Invalid email or password' in data['message']

    def test_login_invalid_password(self, client, create_user):
        """Test login fails with invalid password."""
        create_user(email='user@example.com', password='password123')
        response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login fails with missing fields."""
        response = client.post('/api/auth/login', json={
            'email': 'user@example.com'
            # Missing password
        })
        assert response.status_code == 400


class TestAuthCurrentUser:
    """Test current user endpoint."""

    def test_get_current_user_authenticated(self, client, create_user):
        """Test getting current user when authenticated."""
        user = create_user(email='user@example.com', password='password123')
        
        # Login first
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Get current user
        response = client.get(
            '/api/auth/me',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['email'] == 'user@example.com'
        assert data['name'] == 'Test User'

    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user fails without token."""
        response = client.get('/api/auth/me')
        assert response.status_code == 401


class TestPasswordReset:
    """Test password reset endpoints."""

    def test_request_password_reset(self, client, create_user):
        """Test requesting password reset."""
        create_user(email='user@example.com')
        response = client.post('/api/auth/reset-password', json={
            'email': 'user@example.com'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'reset' in data['message'].lower()

    def test_request_password_reset_nonexistent_user(self, client):
        """Test password reset request for nonexistent user."""
        response = client.post('/api/auth/reset-password', json={
            'email': 'nonexistent@example.com'
        })
        # Should return generic message for security
        assert response.status_code == 200

    def test_confirm_password_reset(self, client, create_user, db_session):
        """Test confirming password reset."""
        import hashlib
        user = create_user(email='user@example.com')
        
        # Generate reset token
        reset_token = 'test-token-123'
        user.reset_password_token = hashlib.sha256(reset_token.encode()).hexdigest()
        from datetime import datetime, timedelta
        user.reset_password_expires = datetime.utcnow() + timedelta(minutes=10)
        db_session.session.commit()
        
        response = client.post('/api/auth/reset-password/confirm', json={
            'token': reset_token,
            'newPassword': 'newpassword123'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'successful' in data['message'].lower()

    def test_confirm_password_reset_expired_token(self, client, create_user, db_session):
        """Test password reset with expired token."""
        import hashlib
        from datetime import datetime, timedelta
        
        user = create_user(email='user@example.com')
        reset_token = 'test-token-123'
        user.reset_password_token = hashlib.sha256(reset_token.encode()).hexdigest()
        user.reset_password_expires = datetime.utcnow() - timedelta(minutes=1)  # Expired
        db_session.session.commit()
        
        response = client.post('/api/auth/reset-password/confirm', json={
            'token': reset_token,
            'newPassword': 'newpassword123'
        })
        assert response.status_code == 400


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_user_cannot_access_admin_endpoints(self, client, create_user):
        """Test regular user cannot access admin endpoints."""
        user = create_user(email='user@example.com', password='password123', role='user')
        
        # Login as user
        login_response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Try to access admin endpoint (e.g., get all members)
        response = client.get(
            '/api/members',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 403

    def test_admin_can_access_admin_endpoints(self, client, create_user):
        """Test admin user can access admin endpoints."""
        admin = create_user(email='admin@example.com', password='password123', role='admin')
        
        # Login as admin
        login_response = client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Access admin endpoint
        response = client.get(
            '/api/members',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
