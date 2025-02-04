from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db
from views import bp

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:parola_baza_date@localhost/ip'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.register_blueprint(bp)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)