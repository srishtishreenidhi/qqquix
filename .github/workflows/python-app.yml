import sys
import os
import pytest
from flask import session

# Add the root directory to sys.path for import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"login" in response.data.lower()

def test_register_page_loads(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b"register" in response.data.lower()

def test_protected_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_quiz_get_requires_login(client):
    response = client.get('/quiz')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_home_with_login(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    response = client.get('/')
    assert response.status_code == 200
    assert b"home" in response.data.lower()
