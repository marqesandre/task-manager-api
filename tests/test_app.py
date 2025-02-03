import pytest
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login(client):
    response = client.post('/auth/login', 
        data=json.dumps({'email': 'test@test.com', 'password': 'test123'}),
        content_type='application/json')
    assert response.status_code in [200, 401]

def test_tasks_without_token(client):
    response = client.get('/tasks')
    assert response.status_code == 401
