from flask import Blueprint, request, jsonify
from models import db, Review
import requests
import os

reviews_bp = Blueprint('reviews', __name__)

CUSTOMERS_SERVICE_URL = os.getenv('CUSTOMERS_SERVICE_URL', 'http://customers_service:5001')
INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://inventory_service:5002')

def customer_exists(username):
    try:
        response = requests.get(f'{CUSTOMERS_SERVICE_URL}/customers/{username}')
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def item_exists(item_name):
    try:
        response = requests.get(f'{INVENTORY_SERVICE_URL}/inventory')
        if response.status_code != 200:
            return False
        items = response.json()
        return any(item['name'].lower() == item_name.lower() for item in items)
    except requests.exceptions.RequestException:
        return False

@reviews_bp.route('/')
def home():
    return jsonify({"message": "Welcome to the Reviews Service!"})

@reviews_bp.route('/', methods=['POST'])
def submit_review():
    data = request.get_json()

    required_fields = ['customer_username', 'item_name', 'rating', 'comment']
    for field in required_fields:
        if field not in data:
            return {'error': f'{field} is required.'}, 400

    customer_username = data['customer_username']
    item_name = data['item_name']
    rating = data['rating']
    comment = data['comment']

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return {'error': 'Rating must be an integer between 1 and 5.'}, 400

    if not customer_exists(customer_username):
        return {'error': 'Customer does not exist.'}, 404

    if not item_exists(item_name):
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

    return {'message': 'Review submitted successfully.', 'review_id': review.id}, 201

@reviews_bp.route('/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    data = request.get_json()

    review = Review.query.get(review_id)
    if not review:
        return {'error': 'Review not found.'}, 404

    customer_username = data.get('customer_username')
    if customer_username != review.customer_username:
        return {'error': 'Unauthorized to update this review.'}, 403

    if 'rating' in data:
        rating = data['rating']
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            return {'error': 'Rating must be an integer between 1 and 5.'}, 400
        review.rating = rating

    if 'comment' in data:
        review.comment = data['comment']

    review.status = 'pending'
    db.session.commit()

    return {'message': 'Review updated successfully.'}, 200

@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return {'error': 'Review not found.'}, 404

    customer_username = request.args.get('customer_username')
    if customer_username != review.customer_username:
        return {'error': 'Unauthorized to delete this review.'}, 403

    db.session.delete(review)
    db.session.commit()

    return {'message': 'Review deleted successfully.'}, 200

@reviews_bp.route('/product/<string:item_name>', methods=['GET'])
def get_product_reviews(item_name):
    reviews = Review.query.filter_by(item_name=item_name, status='approved').all()
    reviews_list = [review.to_dict() for review in reviews]
    return jsonify(reviews_list), 200

@reviews_bp.route('/customer/<string:customer_username>', methods=['GET'])
def get_customer_reviews(customer_username):
    reviews = Review.query.filter_by(customer_username=customer_username).all()
    reviews_list = [review.to_dict() for review in reviews]
    return jsonify(reviews_list), 200

@reviews_bp.route('/<int:review_id>/moderate', methods=['PUT'])
def moderate_review(review_id):
    data = request.get_json()

    review = Review.query.get(review_id)
    if not review:
        return {'error': 'Review not found.'}, 404

    if 'status' not in data or data['status'] not in ['approved', 'rejected']:
        return {'error': 'Invalid status. Must be "approved" or "rejected".'}, 400

    review.status = data['status']
    db.session.commit()

    return {'message': f'Review {review.status} successfully.'}, 200

@reviews_bp.route('/<int:review_id>', methods=['GET'])
def get_review_details(review_id):
    review = Review.query.get(review_id)
    if not review:
        return {'error': 'Review not found.'}, 404

    return jsonify(review.to_dict()), 200
