from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm, file
from wtforms import fields, widgets, validators

import datetime

from .fields import TagListField, TextListField

from viyyoor import models


BaseDigitalCertificateForm = model_form(
    models.DigitalCertificate,
    FlaskForm,
    exclude=["created_date", "ip_address", "file", "owner", "status", "password"],
    field_args={"ca_download_url": {"label": "CA Download URL"}},
)


class DigitalCertificateForm(BaseDigitalCertificateForm):
    digital_certificate_file = fields.FileField(
        "Digital Certificate File", validators=[file.FileAllowed(["p12"], "allow p12")]
    )
    password = fields.PasswordField("Password", validators=[validators.InputRequired()])
