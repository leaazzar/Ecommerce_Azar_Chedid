from flask import Blueprint, request, jsonify
from models import Purchase
from db import db
import requests
import os

sales_bp = Blueprint('sales_bp', __name__)

INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://inventory_service:5002')
CUSTOMERS_SERVICE_URL = os.getenv('CUSTOMERS_SERVICE_URL', 'http://customers_service:5001')

@sales_bp.route('/')
def home():
    return jsonify({"message": "Welcome to the Sales Service!"})

@sales_bp.route('/goods', methods=['GET'])
def get_goods():
    try:
        inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/inventory')
        if inventory_response.status_code != 200:
            return {"error": "Failed to retrieve goods from Inventory service."}, 500
        inventory_data = inventory_response.json()

        goods_list = []
        for item in inventory_data:
            if item.get('count_in_stock', 0) > 0:
                goods_list.append({
                    'name': item.get('name'),
                    'price_per_item': item.get('price_per_item')
                })

        return jsonify(goods_list), 200

    except requests.exceptions.RequestException:
        return {"error": "Inventory service is unavailable."}, 503
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@sales_bp.route('/goods/<string:good_name>', methods=['GET'])
def get_good_details(good_name):
    try:
        inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/inventory')
        if inventory_response.status_code != 200:
            return {"error": "Failed to retrieve goods from Inventory service."}, 500
        inventory_data = inventory_response.json()

        item = next((item for item in inventory_data if item['name'].lower() == good_name.lower()), None)

        if not item:
            return {"error": "Item not found."}, 404

        return jsonify(item), 200

    except requests.exceptions.RequestException:
        return {"error": "Inventory service is unavailable."}, 503
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@sales_bp.route('/sales', methods=['POST'])
def create_sale():
    try:
        data = request.json
        required_fields = ['customer_username', 'item_name', 'quantity']
        for field in required_fields:
            if field not in data:
                return {"error": f"{field} is required."}, 400

        customer_username = data['customer_username']
        item_name = data['item_name']
        quantity = data['quantity']

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return {"error": "Quantity must be a positive integer."}, 400
        except ValueError:
            return {"error": "Quantity must be a valid integer."}, 400

        # Get Customer Details
        customer_response = requests.get(f'{CUSTOMERS_SERVICE_URL}/customers/{customer_username}')
        if customer_response.status_code != 200:
            return {"error": "Customer not found."}, 404
        customer_data = customer_response.json()
        customer_wallet = customer_data.get('wallet')

        # Get Inventory Data
        inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/inventory')
        if inventory_response.status_code != 200:
            return {"error": "Failed to retrieve goods from Inventory service."}, 500
        inventory_data = inventory_response.json()

        item = next((item for item in inventory_data if item['name'].lower() == item_name.lower()), None)
        if not item:
            return {"error": "Item not found."}, 404

        item_price = item.get('price_per_item')
        count_in_stock = item.get('count_in_stock')
        item_id = item.get('id')

        if count_in_stock < quantity:
            return {"error": "Insufficient stock."}, 400

        total_price = item_price * quantity

        if customer_wallet < total_price:
            return {"error": "Insufficient funds in wallet."}, 400

        # Deduct Money from Wallet
        deduct_wallet_response = requests.post(
            f'{CUSTOMERS_SERVICE_URL}/customers/{customer_username}/deduct',
            json={'amount': total_price}
        )
        if deduct_wallet_response.status_code != 200:
            return {"error": "Failed to deduct from customer wallet."}, 500

        # Update Inventory
        new_count = count_in_stock - quantity
        update_inventory_response = requests.put(
            f'{INVENTORY_SERVICE_URL}/inventory/{item_id}',
            json={'count_in_stock': new_count}
        )
        if update_inventory_response.status_code != 200:
            # Rollback the wallet deduction
            requests.post(
                f'{CUSTOMERS_SERVICE_URL}/customers/{customer_username}/charge',
                json={'amount': total_price}
            )
            return {"error": "Failed to update item in inventory."}, 500

        # Record the Purchase
        purchase = Purchase(
            customer_username=customer_username,
            item_name=item_name,
            quantity=quantity,
            total_price=total_price
        )
        db.session.add(purchase)
        db.session.commit()

        return {"message": "Purchase successful.", "purchase_id": purchase.purchase_id}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@sales_bp.route('/customers/<username>/purchases', methods=['GET'])
def get_purchase_history(username):
    try:
        purchases = Purchase.query.filter_by(customer_username=username).all()
        if not purchases:
            return {"message": "No purchase history found for this customer."}, 200

        purchases_list = [purchase.to_dict() for purchase in purchases]
        return jsonify(purchases_list), 200
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
