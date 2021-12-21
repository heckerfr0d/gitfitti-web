from flask import Flask
from flask_login import LoginManager
import os
from celery import Celery

login_manager = LoginManager()
celery = Celery(__name__, broker=os.getenv('REDIS_URL'), result_backend=os.getenv('REDIS_URL'))

def init_app():
    app = Flask(__name__)
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    celery.conf.update(app.config)
    login_manager.init_app(app)

    with app.app_context():

        from . import routes

        return app