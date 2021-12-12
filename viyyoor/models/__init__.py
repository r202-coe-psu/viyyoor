from flask_mongoengine import MongoEngine

from .users import User
from .oauth2 import OAuth2Token
from .classes import Class

db = MongoEngine()


def init_db(app):
    db.init_app(app)
