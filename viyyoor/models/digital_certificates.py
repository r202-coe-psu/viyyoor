import mongoengine as me
import datetime

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DIGITAL_CERTIFICATE_CHOICES = [("self", "Self Signed"), ("psusigner", "PSU Signer")]


class SignerAPI(me.EmbeddedDocument):
    code = me.StringField(max_length=255)
    secret = me.BinaryField()
    agent_key = me.BinaryField()
    jwt_secret = me.BinaryField()
    api_url = me.StringField(max_length=1024)


class DigitalCertificate(me.Document):
    meta = {"collection": "digital_certificates"}

    type_ = me.StringField(
        required=True, choices=DIGITAL_CERTIFICATE_CHOICES, default="self"
    )

    signer_api = me.EmbeddedDocumentField(SignerAPI, default=SignerAPI())

    file = me.FileField(collection_name="digital_certificate_fs")
    password = me.BinaryField()
    ca_download_url = me.StringField(max_length=1024)

    owner = me.ReferenceField("User", dbref=True, required=True)
    updated_by = me.ReferenceField("User", dbref=True, required=True)
    status = me.StringField(required=True, default="active")

    subject = me.StringField(required=True, default="")
    issuer = me.StringField(required=True, default="")

    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    expired_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    ip_address = me.StringField(required=True, default="0.0.0.0")

    def get_key(self):
        password = self.ip_address.encode()
        salt = str(self.owner.id).rjust(16, "0")[:16].encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
        )
        # data = str(self.owner.id).rjust(32, "0")[:32]
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def encrypt_password(self, password):
        key = self.get_key()
        f = Fernet(key)
        password_byte = password
        if type(password) == str:
            password_byte = password.encode()
        return f.encrypt(password_byte)

    def decrypt_password(self, token):
        key = self.get_key()
        f = Fernet(key)
        return f.decrypt(token)
