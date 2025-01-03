from flask import Blueprint, request, jsonify
from models import Purchase
from db import db
import requests
import os
from sqlalchemy.sql import text

import logging

logging.basicConfig(
    filename='sales_service.log',  # Log file name
    level=logging.INFO,            # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

sales_bp = Blueprint('sales_bp', __name__)

INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://ecommerce_azar_chedid-inventory_service-1:5002/api/v1')
CUSTOMERS_SERVICE_URL = os.getenv('CUSTOMERS_SERVICE_URL', 'http://ecommerce_azar_chedid-customers_service-1:5001/api/v1')
@sales_bp.route('/health', methods=['GET'])
def health_check():
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        database_status = "Healthy"
    except Exception as e:
        database_status = f"Unhealthy: {str(e)}"

    # Check external services (Example: Inventory Service and Customer Service)
    try:
        inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/health')
        inventory_service_status = "Healthy" if inventory_response.status_code == 200 else "Unhealthy"
    except Exception as e:
        inventory_service_status = f"Unhealthy: {str(e)}"

    try:
        customer_response = requests.get(f'{CUSTOMERS_SERVICE_URL}/health')
        customer_service_status = "Healthy" if customer_response.status_code == 200 else "Unhealthy"
    except Exception as e:
        customer_service_status = f"Unhealthy: {str(e)}"

    # Aggregate results
    overall_status = "Healthy" if database_status == "Healthy" and inventory_service_status == "Healthy" and customer_service_status == "Healthy" else "Unhealthy"

    return jsonify({
        "database": database_status,
        "inventory_service": inventory_service_status,
        "customer_service": customer_service_status,
        "status": overall_status
    })

@sales_bp.route('/')
def home():
    logging.info("Accessed the home route.")
    return jsonify({"message": "Welcome to the Sales Service!"})

@sales_bp.route('/goods', methods=['GET'])
def get_goods():
    try:
        logging.info("Fetching goods from the Inventory service.")
        inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/inventory', timeout=5)
        inventory_response.raise_for_status()
        inventory_data = inventory_response.json()

        goods_list = [
            {'name': item.get('name'), 'price_per_item': item.get('price_per_item')}
            for item in inventory_data if item.get('count_in_stock', 0) > 0
        ]

        logging.info(f"Successfully fetched {len(goods_list)} goods.")
        return jsonify(goods_list), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching goods: {str(e)}")
        return {"error": "Inventory service is unavailable or timeout occurred."}, 503
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": "An unexpected error occurred."}, 500

@sales_bp.route('/goods/<string:good_name>', methods=['GET'])
def get_good_details(good_name):
    try:
        inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/inventory', timeout=5)
        inventory_response.raise_for_status()

        try:
            inventory_data = inventory_response.json()
        except ValueError:
            return {"error": "Invalid response format from Inventory service."}, 500

        item = next((item for item in inventory_data if item.get('name', '').lower() == good_name.lower()), None)
        
        if not item:
            return {"error": f"Item '{good_name}' not found in inventory."}, 404

        return jsonify(item), 200

    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error occurred while fetching item details: {str(e)}"}, 502
    except requests.exceptions.RequestException:
        return {"error": "Inventory service is unavailable or timeout occurred."}, 503
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@sales_bp.route('/sales', methods=['POST'])
def create_sale():
    try:
        # Log the incoming request
        data = request.json
        logging.info(f"Received sale request: {data}")

        # Validate required fields
        required_fields = ['customer_username', 'item_name', 'quantity']
        for field in required_fields:
            if field not in data:
                logging.warning(f"Missing required field: {field}")
                return {"error": f"{field} is required."}, 400

        customer_username = data['customer_username']
        item_name = data['item_name']
        quantity = data['quantity']

        # Validate quantity
        try:
            quantity = int(quantity)
            if quantity <= 0:
                logging.warning(f"Invalid quantity: {quantity}")
                return {"error": "Quantity must be a positive integer."}, 400
        except ValueError:
            logging.warning(f"Non-integer quantity: {quantity}")
            return {"error": "Quantity must be a valid integer."}, 400

        logging.info(f"Processing sale for customer: {customer_username}, item: {item_name}, quantity: {quantity}")

        # Get Customer Details
        customer_response = requests.get(f'{CUSTOMERS_SERVICE_URL}/customers/{customer_username}')
        if customer_response.status_code != 200:
            logging.warning(f"Customer not found: {customer_username}")
            return {"error": "Customer not found."}, 404
        customer_data = customer_response.json()
        customer_wallet = customer_data.get('wallet')
        logging.info(f"Customer details retrieved: {customer_data}")

        # Get Inventory Data
        inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/inventory')
        if inventory_response.status_code != 200:
            logging.error("Failed to retrieve inventory data.")
            return {"error": "Failed to retrieve goods from Inventory service."}, 500
        inventory_data = inventory_response.json()

        item = next((item for item in inventory_data if item['name'].lower() == item_name.lower()), None)
        if not item:
            logging.warning(f"Item not found: {item_name}")
            return {"error": "Item not found."}, 404

        item_price = item.get('price_per_item')
        count_in_stock = item.get('count_in_stock')
        item_id = item.get('id')

        logging.info(f"Item details retrieved: {item}")

        # Check stock availability
        if count_in_stock < quantity:
            logging.warning(f"Insufficient stock for item: {item_name} (Requested: {quantity}, In Stock: {count_in_stock})")
            return {"error": "Insufficient stock."}, 400

        # Calculate total price
        total_price = item_price * quantity
        if customer_wallet < total_price:
            logging.warning(f"Insufficient funds for customer: {customer_username} (Wallet: {customer_wallet}, Total Price: {total_price})")
            return {"error": "Insufficient funds in wallet."}, 400

        logging.info(f"Total price calculated: {total_price}")

        # Deduct Money from Wallet
        deduct_wallet_response = requests.post(
            f'{CUSTOMERS_SERVICE_URL}/customers/{customer_username}/deduct',
            json={'amount': total_price}
        )
        if deduct_wallet_response.status_code != 200:
            logging.error(f"Failed to deduct amount from customer wallet: {customer_username}")
            return {"error": "Failed to deduct from customer wallet."}, 500

        logging.info(f"Deducted {total_price} from customer wallet: {customer_username}")

        # Update Inventory
        new_count = count_in_stock - quantity
        update_inventory_response = requests.put(
            f'{INVENTORY_SERVICE_URL}/inventory/{item_id}',
            json={'count_in_stock': new_count}
        )
        if update_inventory_response.status_code != 200:
            logging.error(f"Failed to update inventory for item: {item_name}")
            # Rollback the wallet deduction
            rollback_response = requests.post(
                f'{CUSTOMERS_SERVICE_URL}/customers/{customer_username}/charge',
                json={'amount': total_price}
            )
            if rollback_response.status_code == 200:
                logging.info(f"Wallet deduction rolled back for customer: {customer_username}")
            else:
                logging.error(f"Failed to roll back wallet deduction for customer: {customer_username}")
            return {"error": "Failed to update item in inventory."}, 500

        logging.info(f"Inventory updated for item: {item_name} (New Count: {new_count})")

        # Record the Purchase
        purchase = Purchase(
            customer_username=customer_username,
            item_name=item_name,
            quantity=quantity,
            total_price=total_price
        )
        db.session.add(purchase)
        db.session.commit()

        logging.info(f"Purchase recorded: {purchase}")

        return {"message": "Purchase successful.", "purchase_id": purchase.purchase_id}, 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    
@sales_bp.route('/customers/<username>/purchases', methods=['GET'])
def get_purchase_history(username):
    try:
        purchases = Purchase.query.filter_by(customer_username=username).all()

        # Log the results of the query
        logging.debug(f"Found {len(purchases)} purchases for customer: {username}")

        if not purchases:
            logging.info(f"No purchase history found for customer: {username}")
            return {"message": f"No purchase history found for customer '{username}'."}, 200

        purchases_list = [purchase.to_dict() for purchase in purchases]
        return jsonify(purchases_list), 200
    except Exception as e:
        logging.error(f"Error while fetching purchase history for customer: {username} | {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    
@sales_bp.route('/sales', methods=['GET'])
def get_sales():
        try:
            sales = Purchase.query.all()  # Fetch all sales from the database
            if not sales:
                return jsonify({"message": "No sales found."}), 404
            
            sales_list = [sale.to_dict() for sale in sales]  # Convert sales to dictionary
            return jsonify(sales_list), 200
        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
