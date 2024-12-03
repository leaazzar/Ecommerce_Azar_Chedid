from flask import Flask
from db import db
from routes import sales_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(sales_bp, url_prefix='/sales')

if __name__ == "__main__":
    app.run(debug=True)
