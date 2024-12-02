from flask import Blueprint, request, jsonify
from models import Purchase
from db import db
import requests
import os
import logging

logging.basicConfig(
    filename='sales_service.log',  # Log file name
    level=logging.INFO,            # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

sales_bp = Blueprint('sales_bp', __name__)

INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://ecommerce_azar_chedid-inventory_service-1:5002/api/v1')
CUSTOMERS_SERVICE_URL = os.getenv('CUSTOMERS_SERVICE_URL', 'http://ecommerce_azar_chedid-customers_service-1:5001/api/v1')

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
        # Log the incoming request
        logging.info(f"Received request to fetch purchase history for customer: {username}")

        # Validate username input
        if not username or username.strip() == "":
            logging.warning("Customer username is empty or invalid.")
            return {"error": "Customer username is required and cannot be empty."}, 400

        # Query database for purchases
        purchases = Purchase.query.filter_by(customer_username=username).all()

        # Log the result of the query
        if not purchases:
            logging.info(f"No purchase history found for customer: {username}")
            return {"message": f"No purchase history found for customer '{username}'."}, 200

        logging.info(f"Found {len(purchases)} purchases for customer: {username}")

        # Prepare the list of purchases to return
        purchases_list = [purchase.to_dict() for purchase in purchases]
        logging.info(f"Successfully prepared purchase history for customer: {username}")
        return jsonify(purchases_list), 200

    except ValueError as ve:
        logging.warning(f"Invalid username format for customer: {username} | Error: {str(ve)}")
        return {"error": "Invalid username format."}, 400
    except Exception as e:
        # Handle unexpected errors and log the exception
        logging.error(f"Unexpected error while fetching purchase history for customer: {username} | Error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500