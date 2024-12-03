"""
Database Models for the Inventory Service.

This module contains SQLAlchemy models representing the database schema for the service.
"""
from db import db

class Inventory(db.Model):
    """
    Represents an item in the inventory.

    Attributes:
        id (int): Unique identifier for the item (primary key).
        name (str): Name of the item.
        category (str): Category to which the item belongs.
        price_per_item (float): Price per unit of the item.
        description (str): Description of the item.
        count_in_stock (int): Quantity of the item available in stock.
    """
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g., food, clothes, etc.
    price_per_item = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    count_in_stock = db.Column(db.Integer, nullable=False)
