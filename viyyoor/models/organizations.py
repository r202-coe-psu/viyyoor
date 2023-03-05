import mongoengine as me
import datetime
import markdown
import json


class Logo(me.Document):
    meta = {"collection": "logos"}

    logo_name = me.StringField(required=True, max_length=256)
    logo_file = me.ImageField(
        required=True,
        collection_name="logo_fs",
        size=(3840, 2160, False),
        thumbnail_size=(1920, 1920, False),
    )

    uploaded_by = me.ReferenceField("User", dbref=True)
    uploaded_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    last_updated_by = me.ReferenceField("User", dbref=True)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)
