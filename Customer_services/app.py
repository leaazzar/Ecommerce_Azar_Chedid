import logging
from flask import Flask, jsonify
from db import db
from routes import customers_bp
import os

def create_app():
    app = Flask(__name__)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customers.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(customers_bp, url_prefix='/api/v1')

    # Health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        logging.info("Health check endpoint accessed.")
        return {"status": "ok"}, 200

    # Global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        logging.warning(f"404 error: {error}")
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        logging.error(f"500 error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        logging.warning(f"400 error: {error}")
        return jsonify({"error": "Bad request"}), 400

    return app


if __name__ == '__main__':

    log_file_path = os.path.join(os.getcwd(), 'customers_service.log')
    logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
    print(f"Logging to: {log_file_path}")
    app = create_app()

    # Create tables within the app context
    with app.app_context():
        db.create_all()
        logging.info("Database tables initialized.")

    app.run(host='0.0.0.0', port=5001)
