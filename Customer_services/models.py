"""
Database Models for the Customer Service.

This module contains SQLAlchemy models representing the database schema for the service.
"""
from db import db

class Customer(db.Model):
    """
    Represents a customer in the database.

    Attributes:
         id (:noindex:): The unique identifier for the customer.
        username (:noindex:): The username of the customer.
        full_name (str): Full name of the customer.
        password (str): Password for the customer account (stored securely).
        age (int): Age of the customer.
        gender (str): Gender of the customer (e.g., "Male", "Female", "Other").
        address (str): Address of the customer.
        marital_status (str): Marital status of the customer.
        wallet (float): Wallet balance of the customer.
    """
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200))
    gender = db.Column(db.String(10))
    marital_status = db.Column(db.String(20))
    wallet = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<Customer {self.username}>'
