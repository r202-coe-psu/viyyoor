import mongoengine as me
import datetime

class Certificate(me.Document):
    meta = {"collection": "certificates"}

    class = me.ReferenceField("Class", dbref=True, required=True)

    participant_id = me.StringField(required=True)

    issued_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    owner = me.ReferenceField("User", dbref=True, required=True)
    status = me.StringField(required=True, default="public")

