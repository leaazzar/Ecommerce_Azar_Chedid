from flask import Flask
from db import db
from routes import inventory_bp

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(inventory_bp, url_prefix='/api/v1')

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    print("Registered Routes:")
    print(app.url_map)
    
    app.run(host='0.0.0.0', port=5002)
