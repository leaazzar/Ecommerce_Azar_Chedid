from flask import Blueprint, jsonify, request
from models import db, Review
import requests
import os
import logging
from sqlalchemy.sql import text


logging.basicConfig(
    filename='reviews_service.log',  # Log file name
    level=logging.INFO,              # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)



reviews_bp = Blueprint('reviews', __name__)

INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://ecommerce_azar_chedid-inventory_service-1:5002/api/v1')
CUSTOMERS_SERVICE_URL = os.getenv('CUSTOMERS_SERVICE_URL', 'http://ecommerce_azar_chedid-customers_service-1:5001/api/v1')

def customer_exists(username):
    try:
        response = requests.get(f'{CUSTOMERS_SERVICE_URL}/customers/{username}')
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking if customer exists: {str(e)}")
        return False
    
def item_exists(item_name):
    try:
        response = requests.get(f'{INVENTORY_SERVICE_URL}/inventory')
        if response.status_code != 200:
            return False
        items = response.json()
        return any(item['name'].lower() == item_name.lower() for item in items)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking if item exists: {str(e)}")
        return False

@reviews_bp.route('/health', methods=['GET'])
def health_check():
    """
    Default route for the Reviews Service.

    Provides a welcome message for the service.

    :return: JSON object with a welcome message.
    :rtype: flask.Response
    """
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        database_status = "Healthy"
    except Exception as e:
        database_status = f"Unhealthy: {str(e)}"

    # Check external services (Example: Customer Service and Inventory Service)
    try:
        customer_response = requests.get(f'{CUSTOMERS_SERVICE_URL}/health')
        customer_service_status = "Healthy" if customer_response.status_code == 200 else "Unhealthy"
    except Exception as e:
        customer_service_status = f"Unhealthy: {str(e)}"

    try:
        inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/health')
        inventory_service_status = "Healthy" if inventory_response.status_code == 200 else "Unhealthy"
    except Exception as e:
        inventory_service_status = f"Unhealthy: {str(e)}"

    # Aggregate results
    overall_status = "Healthy" if database_status == "Healthy" and customer_service_status == "Healthy" and inventory_service_status == "Healthy" else "Unhealthy"

    return jsonify({
        "database": database_status,
        "customer_service": customer_service_status,
        "inventory_service": inventory_service_status,
        "status": overall_status
    })

@reviews_bp.route('/')
def home():
    """
    Default route for the Reviews Service.

    Provides a welcome message for the service.

    :return: JSON object with a welcome message.
    :rtype: flask.Response
    """
    logging.info("Accessed home route.")
    return jsonify({"message": "Welcome to the Reviews Service!"})

@reviews_bp.route('/', methods=['POST'])
def submit_review():
    """
    Submit a new review.

    This route allows users to submit reviews for items, which are initially marked as "pending."
    Validations include:
    - Checking required fields.
    - Ensuring the rating is an integer between 1 and 5.
    - Verifying that the customer and item exist.

    :request body: JSON object with the following fields:
        - customer_username (str): Username of the customer submitting the review (required).
        - item_name (str): Name of the item being reviewed (required).
        - rating (int): Rating of the item (1-5, required).
        - comment (str): Comment about the item (required).

    :return: JSON object with a success message and the review ID, or an error message.
    :rtype: flask.Response
    """
    try:
        data = request.get_json()
        logging.info(f"Received review submission: {data}")

        required_fields = ['customer_username', 'item_name', 'rating', 'comment']
        for field in required_fields:
            if field not in data:
                logging.warning(f"Missing required field: {field}")
                return {'error': f'{field} is required.'}, 400

        customer_username = data['customer_username']
        item_name = data['item_name']
        rating = data['rating']
        comment = data['comment']

        if not isinstance(rating, int) or not (1 <= rating <= 5):
            logging.warning(f"Invalid rating: {rating}")
            return {'error': 'Rating must be an integer between 1 and 5.'}, 400

        if not customer_exists(customer_username):
            logging.warning(f"Customer does not exist: {customer_username}")
            return {'error': 'Customer does not exist.'}, 404

        if not item_exists(item_name):
            logging.warning(f"Item does not exist: {item_name}")
            return {'error': 'Item does not exist.'}, 404

        review = Review(
            customer_username=customer_username,
            item_name=item_name,
            rating=rating,
            comment=comment,
            status='pending'
        )
        db.session.add(review)
        db.session.commit()

        logging.info(f"Review submitted successfully: {review}")
        return {'message': 'Review submitted successfully.', 'review_id': review.id}, 201

    except Exception as e:
        logging.error(f"Error submitting review: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    
@reviews_bp.route('/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    """
    Update an existing review.

    Allows users to update the rating and/or comment of a review they submitted.
    The status is reset to "pending" after an update.

    :param review_id: ID of the review to update.
    :type review_id: int
    :request body: JSON object with optional fields:
        - rating (int): Updated rating (1-5).
        - comment (str): Updated comment.

    :return: JSON object with a success message, or an error message.
    :rtype: flask.Response
    """
    try:
        data = request.get_json()
        logging.info(f"Updating review ID {review_id} with data: {data}")

        review = Review.query.get(review_id)
        if not review:
            logging.warning(f"Review not found: ID {review_id}")
            return {'error': 'Review not found.'}, 404

        customer_username = data.get('customer_username')
        if customer_username != review.customer_username:
            logging.warning(f"Unauthorized update attempt by: {customer_username}")
            return {'error': 'Unauthorized to update this review.'}, 403

        if 'rating' in data:
            rating = data['rating']
            if not isinstance(rating, int) or not (1 <= rating <= 5):
                logging.warning(f"Invalid rating during update: {rating}")
                return {'error': 'Rating must be an integer between 1 and 5.'}, 400
            review.rating = rating

        if 'comment' in data:
            review.comment = data['comment']

        review.status = 'pending'
        db.session.commit()

        logging.info(f"Review updated successfully: ID {review_id}")
        return {'message': 'Review updated successfully.'}, 200

    except Exception as e:
        logging.error(f"Error updating review: ID {review_id} | {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    
@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """
    Delete a review.

    Allows users to delete a review they submitted. The user's username must be provided
    as a query parameter to verify authorization.

    :param review_id: ID of the review to delete.
    :type review_id: int
    :query param customer_username: Username of the customer requesting deletion (required).
    :return: JSON object with a success message, or an error message.
    :rtype: flask.Response
    """
    try:
        # Log the incoming delete request
        logging.info(f"Received request to delete review with ID: {review_id}")

        # Retrieve the review from the database
        review = Review.query.get(review_id)
        if not review:
            logging.warning(f"Review not found for ID: {review_id}")
            return {'error': 'Review not found.'}, 404

        # Get customer_username from query parameters
        customer_username = request.args.get('customer_username')
        if not customer_username:
            logging.warning(f"Customer username not provided for review deletion: ID {review_id}")
            return {'error': 'Customer username is required.'}, 400

        # Check if the user is authorized to delete the review
        if customer_username != review.customer_username:
            logging.warning(f"Unauthorized deletion attempt by user: {customer_username} for review ID: {review_id}")
            return {'error': 'Unauthorized to delete this review.'}, 403

        # Perform the deletion
        db.session.delete(review)
        db.session.commit()

        # Log the successful deletion
        logging.info(f"Review with ID: {review_id} successfully deleted by user: {customer_username}")
        return {'message': 'Review deleted successfully.'}, 200

    except Exception as e:
        # Log unexpected errors
        logging.error(f"Error occurred while deleting review with ID: {review_id} | Error: {str(e)}")
        return {'error': f'An unexpected error occurred: {str(e)}'}, 500
    return {'message': 'Review deleted successfully.'}, 200

@reviews_bp.route('/product/<string:item_name>', methods=['GET'])
def get_product_reviews(item_name):
    """
    Retrieve all approved reviews for a specific product.

    Fetches and returns only reviews that are approved for the given item.

    :param item_name: Name of the item whose reviews are to be fetched.
    :type item_name: str
    :return: JSON object with a list of reviews or an appropriate message.
    :rtype: flask.Response
    """
    try:
        # Log the incoming request
        logging.info(f"Received request to fetch reviews for product: {item_name}")

        # Query the database for approved reviews of the specified item
        reviews = Review.query.filter_by(item_name=item_name, status='approved').all()

        if not reviews:
            # Log when no reviews are found
            logging.info(f"No approved reviews found for product: {item_name}")
            return jsonify({"message": f"No reviews found for product '{item_name}'."}), 200

        # Prepare the list of reviews to return
        reviews_list = [review.to_dict() for review in reviews]
        logging.info(f"Found {len(reviews_list)} approved reviews for product: {item_name}")

        # Return the list of reviews
        return jsonify(reviews_list), 200

    except Exception as e:
        # Log unexpected errors
        logging.error(f"Error occurred while fetching reviews for product: {item_name} | Error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@reviews_bp.route('/customer/<string:customer_username>', methods=['GET'])
def get_customer_reviews(customer_username):
    """
    Retrieve all reviews submitted by a specific customer.

    Fetches and returns all reviews (approved, pending, or rejected) submitted by the customer.

    :param customer_username: Username of the customer whose reviews are to be fetched.
    :type customer_username: str
    :return: JSON object with a list of reviews or an appropriate message.
    :rtype: flask.Response
    """

    try:
        # Log the incoming request
        logging.info(f"Received request to fetch reviews for customer: {customer_username}")

        # Query the database for reviews by the customer
        reviews = Review.query.filter_by(customer_username=customer_username).all()

        if not reviews:
            # Log when no reviews are found
            logging.info(f"No reviews found for customer: {customer_username}")
            return jsonify({"message": f"No reviews found for customer '{customer_username}'."}), 200

        # Prepare the list of reviews to return
        reviews_list = [review.to_dict() for review in reviews]
        logging.info(f"Found {len(reviews_list)} reviews for customer: {customer_username}")

        # Return the list of reviews
        return jsonify(reviews_list), 200

    except Exception as e:
        # Log unexpected errors
        logging.error(f"Error occurred while fetching reviews for customer: {customer_username} | Error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@reviews_bp.route('/<int:review_id>/moderate', methods=['PUT'])
def moderate_review(review_id):
    """
    Moderate a review.

    Updates the status of a review to either "approved" or "rejected."

    :param review_id: ID of the review to moderate.
    :type review_id: int
    :request body: JSON object with the following field:
        - status (str): New status for the review ("approved" or "rejected", required).

    :return: JSON object with a success message, or an error message.
    :rtype: flask.Response
    """
    try:
        # Log the incoming moderation request
        logging.info(f"Received request to moderate review with ID: {review_id}")

        # Parse the JSON data from the request
        data = request.get_json()
        if not data:
            logging.warning(f"No data provided for moderating review ID: {review_id}")
            return {'error': 'Request body must contain data.'}, 400

        # Retrieve the review from the database
        review = Review.query.get(review_id)
        if not review:
            logging.warning(f"Review not found for moderation: ID {review_id}")
            return {'error': 'Review not found.'}, 404

        # Validate the status field
        status = data.get('status')
        if status not in ['approved', 'rejected']:
            logging.warning(f"Invalid status provided for review ID: {review_id} | Status: {status}")
            return {'error': 'Invalid status. Must be "approved" or "rejected".'}, 400

        # Update the review status
        review.status = status
        db.session.commit()

        # Log the successful moderation
        logging.info(f"Review with ID: {review_id} successfully moderated to status: {status}")
        return {'message': f'Review {review.status} successfully.'}, 200

    except Exception as e:
        # Log unexpected errors
        logging.error(f"Error occurred while moderating review with ID: {review_id} | Error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@reviews_bp.route('/<int:review_id>', methods=['GET'])
def get_review_details(review_id):
    """
    Retrieve details of a specific review.

    Fetches and returns the details of the review with the specified ID.

    :param review_id: ID of the review to retrieve.
    :type review_id: int
    :return: JSON object with the review details, or an error message.
    :rtype: flask.Response
    """
    try:
        # Log the incoming request
        logging.info(f"Received request to fetch details for review with ID: {review_id}")

        # Retrieve the review from the database
        review = Review.query.get(review_id)
        if not review:
            logging.warning(f"Review not found for ID: {review_id}")
            return {'error': 'Review not found.'}, 404

        # Log the successful retrieval of review details
        logging.info(f"Fetched details for review with ID: {review_id}")
        return jsonify(review.to_dict()), 200

    except Exception as e:
        # Log unexpected errors
        logging.error(f"Error occurred while fetching review details for ID: {review_id} | Error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
