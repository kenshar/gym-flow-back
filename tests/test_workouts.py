import json
from app import db


def auth_headers(client, email, password):
    # register and login to get token
    resp = client.post('/api/auth/register', json={'name': 'Test', 'email': email, 'password': password})
    assert resp.status_code == 201
    token = resp.get_json().get('token')
    return {'Authorization': f'Bearer {token}'}


def test_create_workout_validation(client, create_user):
    headers = auth_headers(client, 'u1@example.com', 'pass')

    # missing type
    resp = client.post('/api/workouts', json={'duration': 30}, headers=headers)
    assert resp.status_code == 400

    # invalid duration
    resp = client.post('/api/workouts', json={'type': 'Cardio', 'duration': 0}, headers=headers)
    assert resp.status_code == 400

    # invalid exercise sets
    payload = {'type': 'Strength Training', 'duration': 30, 'exercises': [{'name': 'Squat', 'sets': 0}]}
    resp = client.post('/api/workouts', json=payload, headers=headers)
    assert resp.status_code == 400


def test_member_ownership_and_admin_permissions(client, create_user, create_member):
    # create two users
    user1 = create_user(email='owner@example.com', name='Owner')
    user2 = create_user(email='other@example.com', name='Other')

    # get auth tokens
    # register API creates users; we will login existing users
    resp = client.post('/api/auth/login', json={'email': 'owner@example.com', 'password': 'password'})
    assert resp.status_code == 200
    token_owner = resp.get_json()['token']

    resp = client.post('/api/auth/login', json={'email': 'other@example.com', 'password': 'password'})
    assert resp.status_code == 200
    token_other = resp.get_json()['token']

    # create a member owned by owner (user1)
    member = create_member(name='Member A', email='a@example.com', user_id=user1.id)

    # other user tries to link workout to member -> should be forbidden
    headers_other = {'Authorization': f'Bearer {token_other}'}
    payload = {'type': 'Cardio', 'duration': 20, 'memberId': member.id}
    resp = client.post('/api/workouts', json=payload, headers=headers_other)
    assert resp.status_code == 403

    # create admin user
    admin = create_user(email='admin@example.com', name='Admin', role='admin')
    resp = client.post('/api/auth/login', json={'email': 'admin@example.com', 'password': 'password'})
    assert resp.status_code == 200
    token_admin = resp.get_json()['token']
    headers_admin = {'Authorization': f'Bearer {token_admin}'}

    # admin can link workout to member
    resp = client.post('/api/workouts', json=payload, headers=headers_admin)
    assert resp.status_code == 201


def test_admin_filter_workouts_by_member(client, create_user, create_member):
    # admin user
    admin = create_user(email='admin2@example.com', name='Admin2', role='admin')
    resp = client.post('/api/auth/login', json={'email': 'admin2@example.com', 'password': 'password'})
    token_admin = resp.get_json()['token']
    headers_admin = {'Authorization': f'Bearer {token_admin}'}

    # owner user
    owner = create_user(email='owner2@example.com', name='Owner2')
    resp = client.post('/api/auth/login', json={'email': 'owner2@example.com', 'password': 'password'})
    token_owner = resp.get_json()['token']
    headers_owner = {'Authorization': f'Bearer {token_owner}'}

    member = create_member(name='Member B', email='b@example.com', user_id=owner.id)

    # owner creates a workout for themselves (member)
    resp = client.post('/api/workouts', json={'type': 'HIIT', 'duration': 25, 'memberId': member.id}, headers=headers_owner)
    assert resp.status_code == 201

    # admin queries workouts by memberId
    resp = client.get(f'/api/workouts?memberId={member.id}', headers=headers_admin)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'workouts' in data
    assert any(w.get('memberId') == member.id for w in data.get('workouts', []))
