from flask import Blueprint, request, jsonify
from models import Customer
from db import db

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers', methods=['POST'])
def register_customer():
    data = request.json
    username = data.get('username')

    # Check if username is unique
    if Customer.query.filter_by(username=username).first():
        return {"error": "Username already taken"}, 400

    customer = Customer(
        full_name=data.get('full_name'),
        username=username,
        password=data.get('password'),
        age=data.get('age'),
        address=data.get('address'),
        gender=data.get('gender'),
        marital_status=data.get('marital_status')
    )
    db.session.add(customer)
    db.session.commit()
    return {"message": "Customer registered successfully"}, 201

@customers_bp.route('/customers', methods=['GET'])
def get_all_customers():
    customers = Customer.query.all()
    return jsonify([{
        "id": c.id,
        "full_name": c.full_name,
        "username": c.username,
        "wallet": c.wallet
    } for c in customers]), 200

@customers_bp.route('/customers/<username>', methods=['GET'])
def get_customer_by_username(username):
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return {"error": "Customer not found"}, 404
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "username": customer.username,
        "wallet": customer.wallet
    }, 200
@customers_bp.route('/customers/<username>', methods=['PUT'])
def update_customer(username):
    data = request.json
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return {"error": "Customer not found"}, 404

    # Update fields
    customer.full_name = data.get('full_name', customer.full_name)
    customer.password = data.get('password', customer.password)
    customer.age = data.get('age', customer.age)
    customer.address = data.get('address', customer.address)
    customer.gender = data.get('gender', customer.gender)
    customer.marital_status = data.get('marital_status', customer.marital_status)
    db.session.commit()
    return {"message": "Customer updated successfully"}, 200

@customers_bp.route('/customers/<username>', methods=['DELETE'])
def delete_customer(username):
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return {"error": "Customer not found"}, 404

    db.session.delete(customer)
    db.session.commit()
    return {"message": "Customer deleted successfully"}, 200

@customers_bp.route('/customers/<username>/charge', methods=['POST'])
def charge_wallet(username):
    data = request.json
    amount = data.get('amount')

    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return {"error": "Customer not found"}, 404

    customer.wallet += amount
    db.session.commit()
    return {"message": f"${amount} added to wallet"}, 200

@customers_bp.route('/customers/<username>/deduct', methods=['POST'])
def deduct_wallet(username):
    data = request.json
    amount = data.get('amount')

    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return {"error": "Customer not found"}, 404

    if customer.wallet < amount:
        return {"error": "Insufficient funds"}, 400

    customer.wallet -= amount
    db.session.commit()
    return {"message": f"${amount} deducted from wallet"}, 200

@customers_bp.route('/customers/<username>', methods=['PUT'])
def update_customer(username):
    data = request.json
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return {"error": "Customer not found"}, 404

    # Update fields
    customer.full_name = data.get('full_name', customer.full_name)
    customer.password = data.get('password', customer.password)
    customer.age = data.get('age', customer.age)
    customer.address = data.get('address', customer.address)
    customer.gender = data.get('gender', customer.gender)
    customer.marital_status = data.get('marital_status', customer.marital_status)
    db.session.commit()
    return {"message": "Customer updated successfully"}, 200

@customers_bp.route('/customers', methods=['GET'])
def get_all_customers():
    customers = Customer.query.all()
    return jsonify([{
        "id": c.id,
        "full_name": c.full_name,
        "username": c.username,
        "wallet": c.wallet
    } for c in customers]), 200


@customers_bp.route('/customers/<username>', methods=['GET'])
def get_customer_by_username(username):
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return {"error": "Customer not found"}, 404
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "username": customer.username,
        "wallet": customer.wallet
    }, 200
