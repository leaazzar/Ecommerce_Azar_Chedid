import pytest
from app import create_app
from db import db
from models import Inventory

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory database for testing

    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()

# Test for adding a new item
def test_add_goods(client):
    response = client.post('/api/v1/inventory', json={
        "name": "Laptop",
        "category": "Electronics",
        "price_per_item": 1000,
        "description": "High-end gaming laptop",
        "count_in_stock": 10
    })
    assert response.status_code == 201
    assert response.json['message'] == "Item added successfully!"

# Test for fetching all items
def test_get_all_goods(client):
    # Add an item first
    client.post('/api/v1/inventory', json={
        "name": "Laptop",
        "category": "Electronics",
        "price_per_item": 1000,
        "description": "High-end gaming laptop",
        "count_in_stock": 10
    })
    response = client.get('/api/v1/inventory')
    assert response.status_code == 200
    assert len(response.json) == 1

# Test for updating an item
def test_update_goods(client):
    # Add an item first
    client.post('/api/v1/inventory', json={
        "name": "Laptop",
        "category": "Electronics",
        "price_per_item": 1000,
        "description": "High-end gaming laptop",
        "count_in_stock": 10
    })
    # Update the item
    response = client.put('/api/v1/inventory/1', json={
        "price_per_item": 1200,
        "count_in_stock": 8
    })
    assert response.status_code == 200
    assert response.json['message'] == "Item updated successfully!"

# Test for deleting an item
def test_deduct_goods(client):
    # Add an item first
    client.post('/api/v1/inventory', json={
        "name": "Laptop",
        "category": "Electronics",
        "price_per_item": 1000,
        "description": "High-end gaming laptop",
        "count_in_stock": 10
    })
    # Delete the item
    response = client.delete('/api/v1/inventory/1')
    assert response.status_code == 200
    assert response.json['message'] == "Item removed successfully!"

# Test for missing required fields
def test_add_goods_missing_fields(client):
    response = client.post('/api/v1/inventory', json={
        "name": "Laptop",
        "category": "Electronics",
    })
    assert response.status_code == 400
    assert "price_per_item is required." in response.json['error']
