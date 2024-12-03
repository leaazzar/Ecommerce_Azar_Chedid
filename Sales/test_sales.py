import pytest
from app import app, db

@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


def test_sales_home(test_client):
    response = test_client.get('/sales/')
    assert response.status_code == 200
    assert response.json == {"message": "Welcome to the Sales Service!"}


def test_sales_create_sale_missing_data(test_client):
    data = {
        "customer_username": "pia",
        "quantity": 1
    }
    response = test_client.post('/sales', json=data)  # Match the route in routes.py
    assert response.status_code == 400

   
    assert response.json == {"error": "item_name is required."}
