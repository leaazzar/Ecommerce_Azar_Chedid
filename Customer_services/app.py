from flask import Flask
from db import db
from routes import customers_bp

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
        return {"status": "ok"}, 200

   

    return app


if __name__ == '__main__':
    app = create_app()

    print("Registered Routes:")
    print(app.url_map)


    # Create tables within the app context
    with app.app_context():
        db.create_all()
        print("Database initialized")

    app.run(host='0.0.0.0', port=5001)
