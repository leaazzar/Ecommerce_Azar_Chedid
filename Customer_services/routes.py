from flask import Blueprint, request, jsonify
from models import Customer
from db import db

customers_bp = Blueprint('customers', __name__)

# Utility function to validate input
def validate_input(data, required_fields):
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"{field} is required.")

@customers_bp.route('/customers', methods=['POST'])
def register_customer():
    try:
        # Parse and validate the request body
        data = request.json
        if data is None:
            return {"error": "Invalid JSON or empty request body."}, 400

        # Validate required fields
        required_fields = ["username", "full_name", "password"]
        for field in required_fields:
            if not data.get(field):
                return {"error": f"{field} is required."}, 400

        # Validate unique username
        if Customer.query.filter_by(username=data.get('username')).first():
            return {"error": "Username already taken"}, 400

        # Validate age
        age = data.get('age')
        if age is not None:
            if not isinstance(age, int):  # Check if age is not already an integer
                try:
                    # Attempt to convert to integer
                    age = int(age)
                except ValueError:
                    return {"error": "Age must be a valid integer."}, 400
            if age < 0:  # Optional: Validate that age is positive
                return {"error": "Age must be a positive integer."}, 400

        # Validate gender
        if data.get('gender') and data.get('gender') not in ["Male", "Female", "Other"]:
            return {"error": "Gender must be 'Male', 'Female', or 'Other'."}, 400

        # Proceed with customer creation
        customer = Customer(
            full_name=data.get('full_name'),
            username=data.get('username'),
            password=data.get('password'),
            age=age,  # Use the validated or converted age
            address=data.get('address'),
            gender=data.get('gender'),
            marital_status=data.get('marital_status')
        )
        db.session.add(customer)
        db.session.commit()

        return {"message": "Customer registered successfully"}, 201

    except Exception as e:
        # Catch all other unexpected exceptions
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@customers_bp.route('/customers', methods=['GET'])
def get_all_customers():
    try:
        # Fetch all customers
        customers = Customer.query.all()

        # Debugging: Print customers to the console
        print("Fetched customers:", customers)

        # Check if customers exist
        if not customers:  # This should trigger if the list is empty
            return {"message": "No customers found."}, 200

        # Return customer data
        return jsonify([{
            "id": c.id,
            "full_name": c.full_name,
            "username": c.username,
            "wallet": c.wallet
        } for c in customers]), 200

    except Exception as e:
        # Handle unexpected errors
        print("Error:", e)  # Debugging error
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500



@customers_bp.route('/customers/<username>', methods=['GET'])
def get_customer_by_username(username):
    try:
        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            return {"error": "Customer not found"}, 404
        return {
            "id": customer.id,
            "full_name": customer.full_name,
            "username": customer.username,
            "wallet": customer.wallet
        }, 200
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@customers_bp.route('/customers/<username>', methods=['PUT'])
def update_customer(username):
    try:
        data = request.json

        # Input validation: Ensure the request body is valid
        if not data or not isinstance(data, dict):
            return {"error": "Invalid JSON or empty request body."}, 400

        # Query the customer by username
        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            return {"error": "Customer not found."}, 404

        # Validate and update fields
        if 'full_name' in data:
            customer.full_name = data['full_name']
        
        if 'password' in data:
            customer.password = data['password']
        
        if 'age' in data:
            try:
                age = int(data['age'])
                if age < 0:
                    return {"error": "Age must be a positive integer."}, 400
                customer.age = age
            except ValueError:
                return {"error": "Age must be a valid integer."}, 400

        if 'address' in data:
            customer.address = data['address']
        
        if 'gender' in data:
            if data['gender'] not in ['Male', 'Female', 'Other']:
                return {"error": "Gender must be 'Male', 'Female', or 'Other'."}, 400
            customer.gender = data['gender']
        
        if 'marital_status' in data:
            customer.marital_status = data['marital_status']

        # Commit the updates
        db.session.commit()
        return {"message": "Customer updated successfully"}, 200

    except Exception as e:
        # Rollback in case of an error
        db.session.rollback()
        # Log the error for debugging (optional)
        print(f"Error updating customer: {e}")
        return {"error": "An unexpected error occurred. Please try again later."}, 500

@customers_bp.route('/customers/<username>', methods=['DELETE'])
def delete_customer(username):
    try:
        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            return {"error": "Customer not found"}, 404

        db.session.delete(customer)
        db.session.commit()
        return {"message": "Customer deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@customers_bp.route('/customers/<username>/charge', methods=['POST'])
def charge_wallet(username):
    try:
        # Validate the request body
        data = request.json
        if not data or not isinstance(data, dict):
            return {"error": "Invalid JSON or empty request body."}, 400

        # Validate the 'amount' field
        amount = data.get('amount')
        if amount is None:
            return {"error": "Amount is required."}, 400
        try:
            amount = float(amount)
            if amount <= 0:
                return {"error": "Amount must be a positive number."}, 400
        except ValueError:
            return {"error": "Amount must be a valid number."}, 400

        # Check if customer exists
        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            return {"error": "Customer not found."}, 404

        # Update the customer's wallet
        customer.wallet += amount
        db.session.commit()

        # Return a success response
        return {"message": f"${amount} added to wallet."}, 200

    except Exception as e:
        # Rollback the transaction in case of errors
        db.session.rollback()

        # Log the error (optional)
        print(f"Error while charging wallet: {e}")

        # Return a generic error response
        return {"error": "An unexpected error occurred. Please try again later."}, 500


@customers_bp.route('/customers/<username>/deduct', methods=['POST'])
def deduct_wallet(username):
    try:
        # Validate the request body
        data = request.json
        if not data or not isinstance(data, dict):
            return {"error": "Invalid JSON or empty request body."}, 400

        # Validate the 'amount' field
        amount = data.get('amount')
        if amount is None:
            return {"error": "Amount is required."}, 400
        try:
            amount = float(amount)
            if amount <= 0:
                return {"error": "Amount must be a positive number."}, 400
        except ValueError:
            return {"error": "Amount must be a valid number."}, 400

        # Check if customer exists
        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            return {"error": "Customer not found."}, 404

        # Check if the wallet has sufficient funds
        if customer.wallet < amount:
            return {"error": "Insufficient funds in wallet."}, 400

        # Deduct the amount from the wallet
        customer.wallet -= amount
        db.session.commit()

        # Return success response
        return {"message": f"${amount} deducted from wallet."}, 200

    except Exception as e:
        # Rollback the transaction in case of errors
        db.session.rollback()

        # Log the error for debugging (optional)
        print(f"Error while deducting wallet: {e}")

        # Return a generic error response
        return {"error": "An unexpected error occurred. Please try again later."}, 500
