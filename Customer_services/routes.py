from flask import Blueprint, request, jsonify
from models import Customer
from db import db
import logging

logging.basicConfig(
    filename='customers_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

customers_bp = Blueprint('customers_bp', __name__)


@customers_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@customers_bp.route('/customers', methods=['POST'])
def register_customer():
    try:
        data = request.json
        if data is None:
            logging.warning("Empty request body for registering customer.")
            return {"error": "Invalid JSON or empty request body."}, 400

        required_fields = ["username", "full_name", "password"]
        for field in required_fields:
            if not data.get(field):
                logging.warning(f"Missing required field: {field}")
                return {"error": f"{field} is required."}, 400

        if Customer.query.filter_by(username=data.get('username')).first():
            logging.warning(f"Username already taken: {data.get('username')}")
            return {"error": "Username already taken"}, 400

        age = data.get('age')
        if age is not None:
            if not isinstance(age, int):
                try:
                    age = int(age)
                except ValueError:
                    logging.warning(f"Invalid age value: {age}")
                    return {"error": "Age must be a valid integer."}, 400
            if age < 0:
                logging.warning(f"Negative age value: {age}")
                return {"error": "Age must be a positive integer."}, 400

        if data.get('gender') and data.get('gender') not in ["Male", "Female", "Other"]:
            logging.warning(f"Invalid gender value: {data.get('gender')}")
            return {"error": "Gender must be 'Male', 'Female', or 'Other'."}, 400

        customer = Customer(
            full_name=data.get('full_name'),
            username=data.get('username'),
            password=data.get('password'),
            age=age,
            address=data.get('address'),
            gender=data.get('gender'),
            marital_status=data.get('marital_status')
        )
        db.session.add(customer)
        db.session.commit()

        logging.info(f"Customer registered successfully: {data.get('username')}")
        return {"message": "Customer registered successfully"}, 201

    except Exception as e:

        logging.error(f"Error while registering customer: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@customers_bp.route('/customers', methods=['GET'])
def get_all_customers():
    try:
        customers = Customer.query.all()
        if not customers:
            logging.info("No customers found in the database.")
            return {"message": "No customers found."}, 200

        logging.info("Fetched all customers.")

        return jsonify([{
            "id": c.id,
            "full_name": c.full_name,
            "username": c.username,
            "wallet": c.wallet
        } for c in customers]), 200

    except Exception as e:

        logging.error(f"Error while fetching all customers: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500



@customers_bp.route('/customers/<username>', methods=['GET'])
def get_customer_by_username(username):
    try:
        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            logging.warning(f"Customer not found: {username}")
            return {"error": "Customer not found"}, 404

        logging.info(f"Customer fetched by username: {username}")
        return {
            "id": customer.id,
            "full_name": customer.full_name,
            "username": customer.username,
            "wallet": customer.wallet
        }, 200

    except Exception as e:
        logging.error(f"Error while fetching customer: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    
@customers_bp.route('/customers/<username>', methods=['PUT'])
def update_customer(username):
    try:
        data = request.json
        if not data or not isinstance(data, dict):
            logging.warning(f"Invalid request body for updating customer: {username}")
            return {"error": "Invalid JSON or empty request body."}, 400

        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            logging.warning(f"Customer not found for update: {username}")
            return {"error": "Customer not found."}, 404
        # Log initial customer data before update
        logging.info(f"Updating customer: {username} | Initial Data: {customer}")

        if 'full_name' in data:
            logging.info(f"Updating full_name for {username}: {data['full_name']}")
            customer.full_name = data['full_name']
        if 'password' in data:
            logging.info(f"Updating password for {username}")
            customer.password = data['password']
        if 'age' in data:
            try:
                age = int(data['age'])
                if age < 0:
                    logging.warning(f"Invalid age value for {username}: {age}")
                    return {"error": "Age must be a positive integer."}, 400
                logging.info(f"Updating age for {username}: {age}")
                customer.age = age
            except ValueError:
                logging.warning(f"Invalid age format for {username}: {data['age']}")
                return {"error": "Age must be a valid integer."}, 400
        if 'address' in data:
            logging.info(f"Updating address for {username}: {data['address']}")
            customer.address = data['address']
        if 'gender' in data:
            if data['gender'] not in ['Male', 'Female', 'Other']:
                logging.warning(f"Invalid gender value for {username}: {data['gender']}")
                return {"error": "Gender must be 'Male', 'Female', or 'Other'."}, 400
            logging.info(f"Updating gender for {username}: {data['gender']}")
            customer.gender = data['gender']
        if 'marital_status' in data:
            logging.info(f"Updating marital_status for {username}: {data['marital_status']}")
            customer.marital_status = data['marital_status']

        db.session.commit()
        logging.info(f"Customer updated successfully: {username} | Updated Data: {customer}")
        return {"message": "Customer updated successfully"}, 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating customer: {username} | Error: {e}")
        return {"error": "An unexpected error occurred. Please try again later."}, 500

@customers_bp.route('/customers/<username>', methods=['DELETE'])
def delete_customer(username):
    try:
        # Log the delete request
        logging.info(f"Received request to delete customer: {username}")

        # Query the customer by username
        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            logging.warning(f"Customer not found for deletion: {username}")
            return {"error": "Customer not found"}, 404

        # Log customer details before deletion
        logging.info(f"Deleting customer: {username} | Details: {customer}")

        # Perform the deletion
        db.session.delete(customer)
        db.session.commit()

        # Log success
        logging.info(f"Customer deleted successfully: {username}")
        return {"message": "Customer deleted successfully"}, 200

    except Exception as e:
        # Rollback in case of an error
        db.session.rollback()

        # Log the error
        logging.error(f"Error deleting customer: {username} | Error: {e}")
        return {"error": "An unexpected error occurred. Please try again later."}, 500

@customers_bp.route('/customers/<username>/charge', methods=['POST'])
def charge_wallet(username):
    try:
        # Log the request
        logging.info(f"Received request to charge wallet for customer: {username}")

        data = request.json
        if not data or not isinstance(data, dict):
            logging.warning(f"Invalid JSON or empty request body for customer: {username}")
            return {"error": "Invalid JSON or empty request body."}, 400

        amount = data.get('amount')
        if amount is None:
            logging.warning(f"Amount field missing in request for customer: {username}")
            return {"error": "Amount is required."}, 400
        try:
            amount = float(amount)
            if amount <= 0:
                logging.warning(f"Invalid amount {amount} for customer: {username}")
                return {"error": "Amount must be a positive number."}, 400
        except ValueError:
            logging.warning(f"Non-numeric amount provided for customer: {username}")
            return {"error": "Amount must be a valid number."}, 400

        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            logging.warning(f"Customer not found: {username}")
            return {"error": "Customer not found."}, 404
        # Log the charging process
        logging.info(f"Charging ${amount} to customer wallet: {username} | Current balance: {customer.wallet}")

        # Update the customer's wallet
        customer.wallet += amount
        db.session.commit()

        # Log the successful transaction
        logging.info(f"Successfully charged ${amount} to wallet of customer: {username} | New balance: {customer.wallet}")

        # Return a success response

        customer.wallet += amount
        db.session.commit()

        return {"message": f"${amount} added to wallet."}, 200

    except Exception as e:
        db.session.rollback()


        # Log the error
        logging.error(f"Error while charging wallet for customer: {username} | Error: {e}")

        # Return a generic error response

        return {"error": "An unexpected error occurred. Please try again later."}, 500

@customers_bp.route('/customers/<username>/deduct', methods=['POST'])
def deduct_wallet(username):
    try:

        # Log the request
        logging.info(f"Received request to deduct from wallet for customer: {username}")

        # Validate the request body

        data = request.json
        if not data or not isinstance(data, dict):
            logging.warning(f"Invalid JSON or empty request body for customer: {username}")
            return {"error": "Invalid JSON or empty request body."}, 400

        amount = data.get('amount')
        if amount is None:
            logging.warning(f"Amount field missing in request for customer: {username}")
            return {"error": "Amount is required."}, 400
        try:
            amount = float(amount)
            if amount <= 0:
                logging.warning(f"Invalid amount {amount} for customer: {username}")
                return {"error": "Amount must be a positive number."}, 400
        except ValueError:
            logging.warning(f"Non-numeric amount provided for customer: {username}")
            return {"error": "Amount must be a valid number."}, 400

        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            logging.warning(f"Customer not found: {username}")
            return {"error": "Customer not found."}, 404

        if customer.wallet < amount:
            logging.warning(f"Insufficient funds: Attempt to deduct ${amount} from customer: {username} with wallet balance: {customer.wallet}")
            return {"error": "Insufficient funds in wallet."}, 400


        # Deduct the amount from the wallet
        logging.info(f"Deducting ${amount} from customer wallet: {username} | Current balance: {customer.wallet}")
        customer.wallet -= amount
        db.session.commit()

        # Log successful deduction
        logging.info(f"Successfully deducted ${amount} from wallet of customer: {username} | New balance: {customer.wallet}")

        # Return success response

        customer.wallet -= amount
        db.session.commit()

        return {"message": f"${amount} deducted from wallet."}, 200

    except Exception as e:
        db.session.rollback()


        # Log the error
        logging.error(f"Error while deducting wallet for customer: {username} | Error: {e}")

        # Return a generic error response
        return {"error": "An unexpected error occurred. Please try again later."}, 500

        return {"error": "An unexpected error occurred. Please try again later."}, 500

