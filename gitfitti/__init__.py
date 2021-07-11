from flask import Flask
from psycopg2 import connect

# DATABASE_URL = os.environ['DATABASE_URL']
# g.conn = connect(DATABASE_URL, sslmode='require')


def init_app():
    app = Flask(__name__)

    with app.app_context():

        from . import routes

        return app