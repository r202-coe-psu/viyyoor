import mongoengine as me
import datetime


SHARE_STATUS_CHOICES = [("unshared", "Unshared"), ("shared", "Shared"), ("public", "Public")]

<<<<<<< HEAD

class Control(me.EmbeddedDocument):
    status = me.StringField(choices=CONTROL_CHOICES, default="unshared", required=True)
    organizations = me.ListField(me.ReferenceField("Organization", dbref=True))
=======
class ShareStatus(me.EmbeddedDocument):
    status = me.StringField(choices=SHARE_STATUS_CHOICES, default="unshared", required=True)
    organizations = me.ListField(me.ReferenceField('Organization', dbref=True))
>>>>>>> 0c0e460ebddcd52738462977481c882f7d3deacb
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


class Logo(me.EmbeddedDocument):
    logo_name = me.ReferenceField("Certificate_logo", dbref=True, required=True)
    logo_file = me.ReferenceField("Certificate_logo", dbref=True, required=True)
    uploaded_date = me.ReferenceField("Certificate_logo", dbref=True, required=True)
