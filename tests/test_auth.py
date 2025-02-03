import pytest
from app import create_app
from app.extensions import mongo, redis_client
import json

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['MONGO_URI'] = 'mongodb://mongodb:27017/taskmanager_test'
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def cleanup():
    yield
    # Clean up the test database after each test
    mongo.db.users.delete_many({})
    for key in redis_client.client.keys('*'):
        redis_client.client.delete(key)

def test_register(client, cleanup):
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'test123',
        'name': 'Test User'
    })
    assert response.status_code == 201
    assert b'User registered successfully' in response.data

def test_login(client, cleanup):
    # First register a user
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'test123',
        'name': 'Test User'
    })
    
    # Then try to login
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'test123'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert 'user' in data

def test_login_invalid_credentials(client, cleanup):
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert b'Invalid credentials' in response.data

def test_logout(client, cleanup):
    # First register and login
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'test123'
    })
    login_response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'test123'
    })
    token = json.loads(login_response.data)['token']
    
    # Then logout
    response = client.post('/api/auth/logout', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    assert b'Logged out successfully' in response.data 