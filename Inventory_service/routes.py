import logging
from flask import Blueprint, request, jsonify
from models import Inventory
from db import db


inventory_bp = Blueprint('inventory', __name__)

logging.basicConfig(
    filename='inventory_service.log',  # Log file
    level=logging.INFO,  # Logging level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)


@inventory_bp.route('/', methods=['GET'])
def default_route():
    logging.info("Default route accessed.")
    return {"message": "Welcome to the Inventory Service!"}, 200

@inventory_bp.route('/inventory', methods=['POST'])
def add_goods():
    try:
        logging.info("Request received to add a new good.")
        data = request.json
        required_fields = ['name', 'category', 'price_per_item', 'count_in_stock']

        for field in required_fields:
            if not data.get(field):
                logging.warning(f"Missing required field: {field}")
                return {"error": f"{field} is required."}, 400

        item = Inventory(
            name=data['name'],
            category=data['category'],
            price_per_item=data['price_per_item'],
            description=data.get('description'),
            count_in_stock=data['count_in_stock']
        )
        db.session.add(item)
        db.session.commit()
        logging.info(f"Good added successfully: {data['name']}")
        return {"message": "Item added successfully!"}, 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error while adding good: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    
@inventory_bp.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_goods(item_id):
    try:
        logging.info(f"Request received to delete item with ID: {item_id}")
        item = Inventory.query.get(item_id)
        if not item:
            logging.warning(f"Item with ID {item_id} not found.")
            return {"error": "Item not found."}, 404

        db.session.delete(item)
        db.session.commit()
        logging.info(f"Item with ID {item_id} deleted successfully.")
        return {"message": "Item removed successfully!"}, 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error while deleting item with ID {item_id}: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@inventory_bp.route('/inventory/<int:item_id>', methods=['PUT'])
def update_goods(item_id):
    try:
        logging.info(f"Request received to update item with ID: {item_id}")
        data = request.json
        item = Inventory.query.get(item_id)
        if not item:
            logging.warning(f"Item with ID {item_id} not found.")
            return {"error": "Item not found."}, 404

        item.name = data.get('name', item.name)
        item.category = data.get('category', item.category)
        item.price_per_item = data.get('price_per_item', item.price_per_item)
        item.description = data.get('description', item.description)
        item.count_in_stock = data.get('count_in_stock', item.count_in_stock)
        db.session.commit()
        logging.info(f"Item with ID {item_id} updated successfully.")
        return {"message": "Item updated successfully!"}, 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error while updating item with ID {item_id}: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    
@inventory_bp.route('/inventory', methods=['GET'])
def get_all_goods():
    try:
        logging.info("Request received to fetch all goods.")
        items = Inventory.query.all()
        if not items:
            logging.info("No goods found in inventory.")
            return {"message": "No items in inventory."}, 200

        logging.info(f"Fetched {len(items)} goods from inventory.")
        return jsonify([{
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price_per_item": item.price_per_item,
            "description": item.description,
            "count_in_stock": item.count_in_stock
        } for item in items]), 200
    except Exception as e:
        logging.error(f"Error while fetching all goods: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500