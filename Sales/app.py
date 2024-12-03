from flask import Flask
from db import db
from routes import sales_bp
import os
import logging

def create_app():
    """Application factory function."""
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(sales_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    # Create the app instance
    app = create_app()

    # Configure logging
    log_file_path = os.path.join(os.getcwd(), 'sales_service.log')
    logging.basicConfig(
        filename=log_file_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5003)
