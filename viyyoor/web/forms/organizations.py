from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm, file
from wtforms import fields, widgets, validators

from viyyoor import models

BaseOrganizationForm = model_form(
    models.Organization,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "created_by",
        "last_updated_by",
        "status",
    ],
    field_args={
        "name": {"label": "Name"},
        "description": {"label": "Desctiption"},
        "quota": {"label": "Quota"},
    },
)


class OrganizationForm(BaseOrganizationForm):
    pass


BaseOrganizationLogoForm = model_form(
    models.CertificateLogo,
    FlaskForm,
    only=["logo_name"],
    field_args={
        "logo_name": {"label": "Logo Name"},
    },
)


class OrganizationLogoForm(BaseOrganizationLogoForm):
    uploaded_logo_file = file.FileField(
        "Logo File",
        validators=[
            validators.input_required(),
            file.FileAllowed(["png", "jpg"], "รับเฉพาะไฟล์ png เเละ jpg เท่านั้น"),
        ],
    )


class OrganizationUserRoleForm(FlaskForm):
    users = fields.SelectMultipleField("")


BaseOrganizationUserRoleChangeForm = model_form(
    models.OrganizationUserRole,
    FlaskForm,
    only=["role"],
    field_args={"role": {"label": ""}},
)


class OrganizationRoleSelectionForm(BaseOrganizationUserRoleChangeForm):
    pass


class OrgnaizationAddMemberForm(FlaskForm):
    members = fields.SelectMultipleField("Select Members")


class AdminOrganizationEditForm(FlaskForm):
    name = fields.StringField("Name")
    description = fields.StringField("Description")
