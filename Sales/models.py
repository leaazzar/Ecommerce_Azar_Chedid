
from datetime import datetime

from db import db

class Purchase(db.Model):
    __tablename__ = 'purchases'

    purchase_id = db.Column(db.Integer, primary_key=True)
    customer_username = db.Column(db.String(80), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'purchase_id': self.purchase_id,
            'customer_username': self.customer_username,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'purchase_date': self.purchase_date.isoformat()
        }
