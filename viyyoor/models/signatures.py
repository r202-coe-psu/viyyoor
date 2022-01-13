import mongoengine as me
import datetime


class Signature(me.Document):
    meta = {"collection": "signatures"}

    owner = me.ReferenceField("User", dbref=True, required=True)
    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    status = me.StringField(required=True, default="active")
    file = me.FileField(required=True, collection_name="signature_fs")

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    ip_address = me.StringField(required=True, default="0.0.0.0")
