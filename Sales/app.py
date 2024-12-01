# app.py
from flask import Flask
from db import db
from routes import sales_bp

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Register blueprints
app.register_blueprint(sales_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
