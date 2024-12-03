import pytest
from app import create_app
from db import db
from models import Customer

@pytest.fixture
def test_client():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database for testing
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create all tables
        yield client

    # Cleanup after test
    with app.app_context():
        db.drop_all()

def test_register_customer(test_client):
    payload = {
        "full_name": "John Doe",
        "username": "johndoe",
        "password": "password123",
        "age": 30,
        "address": "123 Elm Street",
        "gender": "Male",
        "marital_status": "Single"
    }
    response = test_client.post('/api/v1/customers', json=payload)
    assert response.status_code == 201
    assert response.json["message"] == "Customer registered successfully"

def test_get_all_customers(test_client):
    # Add a test customer to the database
    with test_client.application.app_context():
        customer = Customer(
            full_name="Jane Doe",
            username="janedoe",
            password="password123",
            age=28,
            address="456 Oak Street",
            gender="Female",
            marital_status="Married"
        )
        db.session.add(customer)
        db.session.commit()

    # Test retrieving all customers
    response = test_client.get('/api/v1/customers')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["username"] == "janedoe"

def test_get_customer_by_username(test_client):
    # Add a test customer to the database
    with test_client.application.app_context():
        customer = Customer(
            full_name="Alice Doe",
            username="alicedoe",
            password="password456",
            age=25,
            address="789 Pine Street",
            gender="Female",
            marital_status="Single"
        )
        db.session.add(customer)
        db.session.commit()

    # Test retrieving the customer by username
    response = test_client.get('/api/v1/customers/alicedoe')
    assert response.status_code == 200
    assert response.json["username"] == "alicedoe"

def test_update_customer(test_client):
    # Add a test customer to the database
    with test_client.application.app_context():
        customer = Customer(
            full_name="Bob Doe",
            username="bobdoe",
            password="password789",
            age=35,
            address="123 Elm Street",
            gender="Male",
            marital_status="Married"
        )
        db.session.add(customer)
        db.session.commit()

    # Test updating the customer's full name
    payload = {"full_name": "Robert Doe"}
    response = test_client.put('/api/v1/customers/bobdoe', json=payload)
    assert response.status_code == 200
    assert response.json["message"] == "Customer updated successfully"

    # Verify the update in the database
    updated_customer = Customer.query.filter_by(username="bobdoe").first()
    assert updated_customer.full_name == "Robert Doe"

def test_delete_customer(test_client):
    # Add a test customer to the database
    with test_client.application.app_context():
        customer = Customer(
            full_name="Charlie Doe",
            username="charliedoe",
            password="password000",
            age=40,
            address="789 Pine Street",
            gender="Male",
            marital_status="Divorced"
        )
        db.session.add(customer)
        db.session.commit()

    # Test deleting the customer
    response = test_client.delete('/api/v1/customers/charliedoe')
    assert response.status_code == 200
    assert response.json["message"] == "Customer deleted successfully"

    # Verify the customer is no longer in the database
    deleted_customer = Customer.query.filter_by(username="charliedoe").first()
    assert deleted_customer is None

def test_charge_wallet(test_client):
    # Add a test customer to the database
    with test_client.application.app_context():
        customer = Customer(
            full_name="David Doe",
            username="daviddoe",
            password="password321",
            age=32,
            address="456 Oak Street",
            gender="Male",
            marital_status="Married",
            wallet=50.0
        )
        db.session.add(customer)
        db.session.commit()

    # Test charging the wallet
    payload = {"amount": 25.0}
    response = test_client.post('/api/v1/customers/daviddoe/charge', json=payload)
    assert response.status_code == 200
    assert response.json["message"] == "$25.0 added to wallet."

    # Verify the wallet update
    updated_customer = Customer.query.filter_by(username="daviddoe").first()
    assert updated_customer.wallet == 75.0

def test_deduct_wallet(test_client):
    # Add a test customer to the database
    with test_client.application.app_context():
        customer = Customer(
            full_name="Eve Doe",
            username="evedoe",
            password="password654",
            age=29,
            address="123 Elm Street",
            gender="Female",
            marital_status="Single",
            wallet=100.0
        )
        db.session.add(customer)
        db.session.commit()

    # Test deducting from the wallet
    payload = {"amount": 50.0}
    response = test_client.post('/api/v1/customers/evedoe/deduct', json=payload)
    assert response.status_code == 200
    assert response.json["message"] == "$50.0 deducted from wallet."

    # Verify the wallet update
    updated_customer = Customer.query.filter_by(username="evedoe").first()
    assert updated_customer.wallet == 50.0
