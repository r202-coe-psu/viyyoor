import mongoengine as me
import datetime


SHARE_STATUS_CHOICES = [("unshared", "Unshared"), ("shared", "Shared"), ("public", "Public")]

class ShareStatus(me.EmbeddedDocument):
    status = me.StringField(choices=SHARE_STATUS_CHOICES, default="unshared", required=True)
    organizations = me.ListField(me.ReferenceField('Organization', dbref=True))
    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )

class Template(me.Document):
    meta = {"collection": "templates"}

    name = me.StringField(required=True, max_length=256)
    description = me.StringField()

    tags = me.ListField(me.StringField(required=True))

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    owner = me.ReferenceField("User", dbref=True, required=True)
    last_updated_by = me.ReferenceField("User", dbref=True, required=True)

    status = me.StringField(required=True, default="active")
    share_status = me.EmbeddedDocumentField("ShareStatus", default=ShareStatus)

    template_file = me.FileField(required=True)
    thumbnail_file = me.FileField()
