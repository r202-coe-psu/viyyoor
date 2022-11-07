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
        "endorsers",
        "admins",
    ],
    field_args={
        "name": {"label": "Name"},
        "description": {"label": "Desctiption"},
        "quota": {"label": "Quota"},
    },
)


class OrganizationForm(BaseOrganizationForm):
    admins = fields.SelectMultipleField("Admins")
    uploaded_logos = file.FileField(
        "Logo File",
        validators=[
            file.FileAllowed(["png", "jpg"], "รับเฉพาะไฟล์ png เเละ jpg เท่านั้น")
        ],
    )


class OrganizationAdminsForm(FlaskForm):
    admins = fields.SelectMultipleField("")


class OrganizationEndorsersForm(FlaskForm):
    endorsers = fields.SelectMultipleField("")
