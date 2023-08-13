from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm, file
from wtforms import fields, widgets, validators, Form

import datetime

from .fields import TagListField, TextListField

from viyyoor import models


BaseDigitalCertificateForm = model_form(
    models.DigitalCertificate,
    FlaskForm,
    only=["ca_download_url", "type_"],
    field_args=dict(
        ca_download_url=dict(label="CA Download URL"), type_=dict(label="Signer Type")
    ),
)

BaseSignerAPIForm = model_form(
    models.SignerAPI,
    Form,
    field_args=dict(
        code=dict(label="Code"),
        api_url=dict(label="API URL"),
        secret=dict(label="Secret", widget=widgets.TextInput()),
        agent_key=dict(label="Agent Key", widget=widgets.TextInput()),
        jwt_secret=dict(label="JWT Secret", widget=widgets.TextInput()),
    ),
)


class SignerAPIForm(BaseSignerAPIForm):
    pass


class DigitalCertificateForm(BaseDigitalCertificateForm):
    signer_api = fields.FormField(SignerAPIForm)
    digital_certificate_file = fields.FileField(
        "Digital Certificate File",
        validators=[file.FileAllowed(["p12"], "allow p12"), validators.Optional()],
    )
    password = fields.PasswordField("Password")
