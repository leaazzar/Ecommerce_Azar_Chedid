import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure the project directory is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routes import reviews_bp  # Correct import for Blueprint
from db import db  # Import SQLAlchemy instance

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory DB for testing
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)  # Initialize SQLAlchemy
    app.register_blueprint(reviews_bp, url_prefix='/reviews')
    with app.app_context():
        db.create_all()  # Create tables
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# Mock Review model
@pytest.fixture
def mock_review():
    with patch('models.Review') as mock_review:
        mock_review.query = MagicMock()
        yield mock_review

# Mock db.session
@pytest.fixture
def mock_db_session():
    with patch('db.session') as mock_db_session:  # Correct patch for db.session
        mock_db_session.commit = MagicMock()
        mock_db_session.add = MagicMock()
        mock_db_session.rollback = MagicMock()
        yield mock_db_session

# Mock requests
@pytest.fixture
def mock_requests():
    with patch('routes.requests') as mock_requests:
        yield mock_requests

# Test the home route
def test_home(client):
    response = client.get('/reviews/')
    assert response.status_code == 200
    assert response.get_json() == {"message": "Welcome to the Reviews Service!"}

# Test review submission
def test_submit_review_success(client, mock_review, mock_db_session, mock_requests):
    mock_requests.get.side_effect = [
        MagicMock(status_code=200),  # Mock customer_exists check
        MagicMock(status_code=200, json=MagicMock(return_value=[{'name': 'item1'}]))  # Mock item_exists check
    ]

    review_data = {
        "customer_username": "testuser",
        "item_name": "item1",
        "rating": 5,
        "comment": "Great product!"
    }

    response = client.post('/reviews/', json=review_data)
    assert response.status_code == 201
    assert response.get_json()["message"] == "Review submitted successfully."

# Test unauthorized review update
def test_update_review_unauthorized(client, mock_review):
    mock_review.query.get.return_value = MagicMock(customer_username="different_user")
    response = client.put('/reviews/1', json={"customer_username": "unauthorized_user"})
    assert response.status_code == 500
    assert response.get_json()["error"] == "Unauthorized to update this review."

# Test delete review unauthorized
def test_delete_review_unauthorized(client, mock_review):
    mock_review.query.get.return_value = MagicMock(customer_username="different_user")
    response = client.delete('/reviews/1', query_string={"customer_username": "unauthorized_user"})
    assert response.status_code == 500
    assert response.get_json()["error"] == "Unauthorized to delete this review."

# Test get product reviews
def test_get_product_reviews(client, mock_review):
    mock_review.query.filter_by.return_value.all.return_value = [
        MagicMock(to_dict=MagicMock(return_value={"item_name": "item1", "rating": 5, "comment": "Great!"}))
    ]
    response = client.get('/reviews/product/item1')
    assert response.status_code == 500
    assert len(response.get_json()) == 1
