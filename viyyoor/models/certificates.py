import mongoengine as me
import datetime

from flask import request, url_for


class Endorsement(me.EmbeddedDocument):
    endorser = me.ReferenceField("User", dbref=True, required=True)
    endorsed_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    digital_signature = me.ReferenceField("DigitalSignature", dbref=True)
    ip_address = me.StringField(required=True, default="0.0.0.0")


class Certificate(me.Document):
    meta = {"collection": "certificates"}

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    participant_id = me.StringField(required=True)

    issued_date = me.DateTimeField()
    signed_date = me.DateTimeField()
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    issuer = me.ReferenceField("User", dbref=True, required=True)
    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    privacy = me.StringField(required=True, default="public")
    status = me.StringField(required=True, default="no-action")
    endorsements = me.MapField(field=me.EmbeddedDocumentField(Endorsement))

    ca_download_url = me.StringField()

    file = me.FileField(required=True, collection_name="certificate_fs")

    def get_validation_url(self):
        validation_url = request.host_url[:-1] + url_for(
            "certificates.view", certificate_id=self.id
        )
        return validation_url
