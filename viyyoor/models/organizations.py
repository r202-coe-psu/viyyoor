import mongoengine as me
import datetime


ORGANIZATION_ROLES = [("staff", "Staff"), ("endorser", "Endorser"), ("admin", "Admin")]


class OrganizationUserRole(me.Document):
    meta = {"collection": "organization_user_roles"}

    organization = me.ReferenceField("Organization", dbref=True, required=True)
    user = me.ReferenceField("User", dbref=True, required=True)
    role = me.StringField(choices=ORGANIZATION_ROLES, default="staff", required=True)
    last_ip_address = me.StringField()
    status = me.StringField(default="active")

    added_by = me.ReferenceField("User", dbref=True, required=True)
    last_modifier = me.ReferenceField("User", dbref=True, required=True)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)


class Organization(me.Document):
    meta = {"collection": "organizations"}

    name = me.StringField(min_length=4, max_length=255, required=True)
    description = me.StringField()
    status = me.StringField(required=True, default="active")

    number_of_uses = me.IntField(require=True, default=0)
    quota = me.IntField(require=True, default=0)

    created_by = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)


class Certificate_logo(me.Document):
    logo_name = me.StringField(required=True)
    logo_file = me.FileField(required=True)
    uploaded_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    @property
    def remaining_quota(self):
        return self.quota - self.number_of_uses

    def get_users(self):
        return OrganizationUserRole.objects(organization=self)
