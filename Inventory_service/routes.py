from flask import Blueprint, request, jsonify
from models import Inventory
from db import db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/', methods=['GET'])
def default_route():
    return {"message": "Welcome to the Inventory Service!"}, 200


@inventory_bp.route('/inventory', methods=['POST'])
def add_goods():
    try:
        data = request.json
        required_fields = ['name', 'category', 'price_per_item', 'count_in_stock']
        
        # Validate required fields
        for field in required_fields:
            if not data.get(field):
                return {"error": f"{field} is required."}, 400
        
        # Create and save item
        item = Inventory(
            name=data['name'],
            category=data['category'],
            price_per_item=data['price_per_item'],
            description=data.get('description'),
            count_in_stock=data['count_in_stock']
        )
        db.session.add(item)
        db.session.commit()
        return {"message": "Item added successfully!"}, 201
    except Exception as e:
        db.session.rollback()
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@inventory_bp.route('/inventory/<int:item_id>', methods=['DELETE'])
def deduct_goods(item_id):
    try:
        item = Inventory.query.get(item_id)
        if not item:
            return {"error": "Item not found."}, 404

        db.session.delete(item)
        db.session.commit()
        return {"message": "Item removed successfully!"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@inventory_bp.route('/inventory/<int:item_id>', methods=['PUT'])
def update_goods(item_id):
    try:
        data = request.json
        item = Inventory.query.get(item_id)
        if not item:
            return {"error": "Item not found."}, 404

        # Update fields
        item.name = data.get('name', item.name)
        item.category = data.get('category', item.category)
        item.price_per_item = data.get('price_per_item', item.price_per_item)
        item.description = data.get('description', item.description)
        item.count_in_stock = data.get('count_in_stock', item.count_in_stock)
        db.session.commit()
        return {"message": "Item updated successfully!"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@inventory_bp.route('/inventory', methods=['GET'])
def get_all_goods():
    try:
        items = Inventory.query.all()
        return jsonify([{
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price_per_item": item.price_per_item,
            "description": item.description,
            "count_in_stock": item.count_in_stock
        } for item in items]), 200
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
