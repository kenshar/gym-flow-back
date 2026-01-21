import pytest
from app import create_app, db
from app.models import User, Member


@pytest.fixture(scope='module')
def test_app():
    app = create_app('default')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret'

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(test_app):
    return test_app.test_client()


@pytest.fixture(scope='function')
def db_session(test_app):
    with test_app.app_context():
        yield db


@pytest.fixture
def create_user(db_session):
    def _create_user(email='user@example.com', name='Test User', password='password', role='user'):
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db_session.session.add(user)
        db_session.session.commit()
        return user
    return _create_user


@pytest.fixture
def create_member(db_session):
    def _create_member(name='Member One', email='member@example.com', user_id=None):
        member = Member(name=name, email=email, user_id=user_id)
        db_session.session.add(member)
        db_session.session.commit()
        return member
    return _create_member
