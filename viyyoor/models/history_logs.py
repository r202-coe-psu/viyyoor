import mongoengine as me
import datetime


class HistoryLog(me.Document):
    action = me.StringField(required=True, max_length=16)
    user = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )
    ip_address = me.StringField(required=True, default="0.0.0.0")

    meta = {"collection": "history_logs"}
