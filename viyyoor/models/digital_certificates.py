import mongoengine as me
import datetime

import base64


class DigitalCertificate(me.Document):
    meta = {"collection": "digital_certificates"}

    file = me.FileField(required=True, collection_name="digital_certificate_fs")
    password = me.BinaryField(required=True, default=b"")
    owner = me.ReferenceField("User", dbref=True, required=True)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    status = me.StringField(required=True, default="active")

    ip_address = me.StringField(required=True, default="0.0.0.0")

    def encrypt_password(self, password):

        data = str(owner.id).rjust(32, "0")[:32]
        key = base64.urlsafe_b64encode(data)
        f = Fernet(key)
        return f.encrypt(password.encode())

    def decrypt_password(self, token):

        data = str(owner.id).rjust(32, "0")[:32]
        key = base64.urlsafe_b64encode(data)
        f = Fernet(key)
        return f.decrypt(token)
