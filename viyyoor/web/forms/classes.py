from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm, file
from wtforms import fields, widgets, validators

import datetime

from .fields import TagListField, TextListField

from viyyoor import models

BaseClassForm = model_form(
    models.Class,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "participants",
        "endorsers",
        "certificates",
        "status",
    ],
    field_args={
        "name": {"label": "Name"},
        "description": {
            "label": "Desctiption",
        },
        "started_date": {
            "label": "Start Date",
            "format": "%Y-%m-%d",
        },
        "ended_date": {
            "label": "End Date",
            "format": "%Y-%m-%d",
        },
        "issued_date": {
            "label": "Issued Date",
            "format": "%Y-%m-%d",
        },
    },
)


class ClassForm(BaseClassForm):
    tags = TagListField("Tags")
    instructors = TagListField("Instructors")


BaseEndorserForm = model_form(
    models.Endorser,
    FlaskForm,
    exclude=[
        "user",
        "updated_date",
        "last_updated_by",
    ],
    field_args={
        "position": {"label": "Position"},
        "endorser_id": {"label": "Endorse ID"},
        "name": {"label": "Name"},
    },
)


class EndorserForm(BaseEndorserForm):
    user = fields.SelectField("User")


class EndorserGrantForm(FlaskForm):
    users = fields.SelectMultipleField("Users")


BaseParticipantForm = model_form(
    models.Participant,
    FlaskForm,
    exclude=["updated_date", "last_updated_by", "extra"],
    field_args={
        "participant_id": {"label": "Participant ID"},
        "name": {"label": "Name"},
        "extra": {"label": "Extra"},
        "group": {"label": "Group"},
    },
)


class ParticipantForm(BaseParticipantForm):
    extra_data = fields.TextAreaField("Extra Data")


class ParticipantFileForm(FlaskForm):
    participant_file = file.FileField(
        "Participant File", validators=[file.FileRequired()]
    )


BaseCertificateTemplateForm = model_form(
    models.CertificateTemplate,
    FlaskForm,
    exclude=["updated_date", "last_updated_by", "template"],
    field_args={
        "name": {"label": "Name"},
        "appreciate_text": {"label": "Appreciate Text"},
        "group": {"label": "Group"},
    },
)


class CertificateTemplateForm(BaseCertificateTemplateForm):
    template = fields.SelectField("Template", validators=[validators.InputRequired()])


class EndorsementForm(FlaskForm):
    password = fields.PasswordField("Password")
