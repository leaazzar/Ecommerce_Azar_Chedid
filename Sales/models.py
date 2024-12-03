"""
Database Models for the sales Service.

This module contains SQLAlchemy models representing the database schema for the service.
"""
from db import db

class Purchase(db.Model):
    """
    Represents a purchase made by a customer.

    Attributes:
        id (int): Unique identifier for the purchase (primary key).
        customer_username (str): Username of the customer who made the purchase.
        item_name (str): Name of the item purchased.
        quantity (int): Quantity of the item purchased.
        total_price (float): Total price of the purchase.
    """
    __tablename__ = 'purchases'
    purchase_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_username = db.Column(db.String(80), nullable=False)
    item_name = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=db.func.now())

    def to_dict(self):
        return {
            "purchase_id": self.purchase_id,
            "customer_username": self.customer_username,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "total_price": self.total_price,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None
        }
