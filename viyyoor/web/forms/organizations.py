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

BaseOrganizationLogoForm = model_form(
    models.Certificate_logo,
    FlaskForm,
    exclude=["uploaded_date"],
    field_args={
        "logo_name": {"label": "Logo Name"},
    },
)


class OrganizationForm(BaseOrganizationForm):
    pass


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


class OrganizationRoleSelectionForm(FlaskForm):
    role = fields.SelectField(
        default="",
        choices=[
            ("", "Select"),
            ("staff", "Staff"),
            ("admin", "Admin"),
            ("endorser", "Endorser"),
        ],
    )
