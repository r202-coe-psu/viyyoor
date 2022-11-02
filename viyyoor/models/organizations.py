import mongoengine as me
import datetime



class Endorser(me.EmbeddedDocument):
    user = me.ReferenceField("User", dbref=True, required=True) 
    created_by = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)


class Administrator(me.EmbeddedDocument):
    users = me.ReferenceField("User", dbref=True, required=True)
    added_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )


class Organization(me.Document):
    meta = {"collection": "organizations"}

    name = me.StringField(min_length=4, max_length=255, required=True)
    description = me.StringField()
    status = me.StringField(required=True, default="active")
    endorsers = me.ListField(me.EmbeddedDocumentField(Endorser))
    admins = me.ListField(me.EmbeddedDocumentField(Administrator))

    number_of_uses = me.IntField(require=True, default=0)
    quota = me.IntField(require=True, default=0)

    created_by = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    @property
    def remaining_quota(self):
        return self.quota - self.number_of_uses

