from flask_mongoengine import MongoEngine

from .users import User
from .oauth2 import OAuth2Token
from .classes import Class, Endorser, Participant, CertificateTemplate
from .templates import Template
from .signatures import Signature, DigitalSignature
from .certificates import Certificate, Endorsement

db = MongoEngine()


def init_db(app):
    db.init_app(app)
