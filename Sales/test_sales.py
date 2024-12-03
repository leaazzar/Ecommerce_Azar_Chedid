import pytest
from Sales.db import db
from Sales.app import create_app
from models import Purchase
from unittest.mock import patch




class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture
def app():
    app = create_app()
    app.config.from_object(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def init_database(app):
    with app.app_context():
        purchase = Purchase(
            customer_username="test_user",
            item_name="Widget",
            quantity=2,
            total_price=20
        )
        db.session.add(purchase)
        db.session.commit()


# Test: Home Route
def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json['message'] == "Welcome to the Sales Service!"


# Test: Get Goods
@patch('requests.get')
def test_get_goods(mock_get, client):
    mock_inventory_data = [
        {"name": "Widget", "price_per_item": 10, "count_in_stock": 5},
        {"name": "Gadget", "price_per_item": 15, "count_in_stock": 0}
    ]
    mock_get.return_value.json = lambda: mock_inventory_data
    mock_get.return_value.status_code = 200

    response = client.get('/goods')
    assert response.status_code == 200
    goods = response.json
    assert len(goods) == 1
    assert goods[0]['name'] == "Widget"


# Test: Get Good Details
@patch('requests.get')
def test_get_good_details(mock_get, client):
    mock_inventory_data = [{"name": "Widget", "price_per_item": 10, "count_in_stock": 5}]
    mock_get.return_value.json = lambda: mock_inventory_data
    mock_get.return_value.status_code = 200

    response = client.get('/goods/Widget')
    assert response.status_code == 200
    assert response.json['name'] == "Widget"

    response = client.get('/goods/NonexistentItem')
    assert response.status_code == 404
    assert response.json['error'] == "Item 'NonexistentItem' not found in inventory."


# Test: Create Sale
@patch('requests.get')
@patch('requests.post')
@patch('requests.put')
def test_create_sale(mock_put, mock_post, mock_get, client, init_database):
    mock_customer_data = {"username": "test_user", "wallet": 100}
    mock_inventory_data = [
        {"id": 1, "name": "Widget", "price_per_item": 10, "count_in_stock": 5}
    ]

    mock_get.side_effect = [
        # Customer data
        type('Response', (object,), {"json": lambda: mock_customer_data, "status_code": 200}),
        # Inventory data
        type('Response', (object,), {"json": lambda: mock_inventory_data, "status_code": 200}),
    ]
    mock_post.return_value.status_code = 200  # Wallet deduction
    mock_put.return_value.status_code = 200  # Inventory update

    data = {"customer_username": "test_user", "item_name": "Widget", "quantity": 2}
    response = client.post('/sales', json=data)
    assert response.status_code == 201
    assert response.json['message'] == "Purchase successful."

    # Insufficient Stock
    data['quantity'] = 10
    response = client.post('/sales', json=data)
    assert response.status_code == 400
    assert response.json['error'] == "Insufficient stock."


# Test: Get Purchase History
def test_get_purchase_history(client, init_database):
    response = client.get('/customers/test_user/purchases')
    assert response.status_code == 200
    purchases = response.json
    assert len(purchases) > 0
    assert purchases[0]['customer_username'] == "test_user"

    # No purchase history
    response = client.get('/customers/nonexistent_user/purchases')
    assert response.status_code == 200
    assert response.json['message'] == "No purchase history found for customer 'nonexistent_user'."
