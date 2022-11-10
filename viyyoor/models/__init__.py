from flask_mongoengine import MongoEngine

from .users import User, UserSetting
from .oauth2 import OAuth2Token
from .classes import Class, Endorser, Participant, CertificateTemplate
from .templates import Template, ShareStatus
from .signatures import Signature
from .certificates import Certificate, Endorsement
from .digital_certificates import DigitalCertificate
from .organizations import (
    Organization,
    OrganizationUserRole,
    Certificate_logo,
    OrganizationQuata,
)
from .history_logs import HistoryLog

db = MongoEngine()


def init_db(app):
    db.init_app(app)


def init_mongoengine(settings):
    import mongoengine as me

    dbname = settings.get("MONGODB_DB")
    host = settings.get("MONGODB_HOST", "localhost")
    port = int(settings.get("MONGODB_PORT", "27017"))
    username = settings.get("MONGODB_USERNAME", "")
    password = settings.get("MONGODB_PASSWORD", "")

    me.connect(db=dbname, host=host, port=port, username=username, password=password)
