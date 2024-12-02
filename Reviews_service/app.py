# app.py

from flask import Flask
from models import db
from routes import reviews_bp
import os
import logging

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'  
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(reviews_bp, url_prefix='/reviews')

    # Create the database tables
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    log_file_path = os.path.join(os.getcwd(), 'reviews_service.log')
    logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
    app.run(host='0.0.0.0', port=5000)
