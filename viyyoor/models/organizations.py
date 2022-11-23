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

    created_by = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    number_of_uses = me.IntField(require=True, default=0)
    quota = me.IntField(require=True, default=0)

    def get_users(self):
        return OrganizationUserRole.objects(organization=self).order_by("-first_name")


class OrganizationQuata(me.Document):
    number_of_uses = me.IntField(require=True, default=0)
    quota = me.IntField(require=True, default=0)

    created_by = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    ip_address = me.StringField(required=True, default="0.0.0.0")

    meta = {"collection": "organization_quatas"}


class CertificateLogo(me.Document):

    meta = {"collection": "certificate_logos"}

    logo_name = me.StringField(required=True, max_length=256)
    logo_file = me.FileField(required=True)
    
    uploaded_by = me.ReferenceField("User", dbref=True)
    uploaded_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    marked_as_organization_logo = me.BooleanField(default=False)

