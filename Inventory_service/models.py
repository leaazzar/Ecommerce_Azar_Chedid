from db import db

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g., food, clothes, etc.
    price_per_item = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    count_in_stock = db.Column(db.Integer, nullable=False)
