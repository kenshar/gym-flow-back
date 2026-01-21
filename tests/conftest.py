import pytest
import os
from app import create_app, db
from app.models import User, Member


@pytest.fixture(scope='session')
def test_app():
    """Create app with test database configuration."""
    # Configure test database to use SQLite in memory
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    app = create_app('default')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def reset_db(test_app):
    """Reset database before each test."""
    with test_app.app_context():
        # Clean up all tables
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        yield
        # Clean up after test
        db.session.remove()


@pytest.fixture(scope='function')
def client(test_app):
    """Test client fixture."""
    with test_app.app_context():
        yield test_app.test_client()


@pytest.fixture(scope='function')
def db_session(test_app):
    """Database session fixture."""
    with test_app.app_context():
        yield db


@pytest.fixture
def create_user(db_session):
    """Factory fixture for creating test users."""
    import uuid
    def _create_user(email=None, name='Test User', password='password', role='user'):
        if email is None:
            email = f'user-{str(uuid.uuid4())[:8]}@example.com'
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db_session.session.add(user)
        db_session.session.commit()
        return user
    return _create_user


@pytest.fixture
def create_member(db_session):
    """Factory fixture for creating test members."""
    import uuid
    def _create_member(name=None, email=None, user_id=None):
        if name is None:
            name = f'Member {str(uuid.uuid4())[:8]}'
        if email is None:
            email = f'member-{str(uuid.uuid4())[:8]}@example.com'
        member = Member(name=name, email=email, user_id=user_id)
        db_session.session.add(member)
        db_session.session.commit()
        return member
    return _create_member
