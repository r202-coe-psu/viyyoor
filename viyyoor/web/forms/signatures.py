from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm, file
from wtforms import fields, widgets

import datetime

from .fields import TagListField, TextListField

from viyyoor import models

BaseSignatureForm = model_form(
    models.Signature,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "status",
        "last_updated_by",
        "owner",
        "file",
        "ip_address",
    ],
    field_args={},
)


class SignatureForm(BaseSignatureForm):
    signature_file = file.FileField(
        "Signature File",
        validators=[file.FileRequired(), file.FileAllowed(["png"], "allow png")],
    )


class SignatureAdminForm(SignatureForm):
    user = fields.SelectField("User")
