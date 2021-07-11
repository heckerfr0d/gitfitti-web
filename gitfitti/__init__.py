from flask import Flask
from flask_login import LoginManager
import os

login_manager = LoginManager()

def init_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    login_manager.init_app(app)

    with app.app_context():

        from . import routes

        return app