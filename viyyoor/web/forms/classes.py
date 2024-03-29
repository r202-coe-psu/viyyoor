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
        "printed_name": {"label": "Printed Name"},
        "description": {
            "label": "Desctiption",
        },
        "class_date_text": {"label": "Class Date Text (Option)"},
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
        "updated_date",
        "last_updated_by",
    ],
    field_args={
        "position": {"label": "Position"},
        "endorser_id": {"label": "Endorse ID"},
        "name": {"label": "Name"},
        "user": {
            "label": "User",
            "label_modifier": lambda u: f"{u.first_name} {u.last_name}",
        },
    },
)


class EndorserForm(BaseEndorserForm):
    pass


class EndorserGrantForm(FlaskForm):
    users = fields.SelectMultipleField("Users")


BaseParticipantForm = model_form(
    models.Participant,
    FlaskForm,
    exclude=["updated_date", "last_updated_by", "extra"],
    field_args={
        "common_id": {"label": "Common ID"},
        "name": {"label": "Name"},
        "extra": {"label": "Extra"},
        "group": {"label": "Group"},
        "email": {"label": "Email"},
        "organization": {"label": "Organization"},
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
        "certificate_text": {"label": "Certificate Text"},
        "group": {"label": "Group"},
        "organization_name": {"label": "Organization Name"},
        "declaration_text": {"label": "Declaration Text"},
        "remark": {"label": "Remark"},
    },
)


class CertificateTemplateForm(BaseCertificateTemplateForm):
    template = fields.SelectField("Template", validators=[validators.InputRequired()])


class EndorsementForm(FlaskForm):
    password = fields.PasswordField("Password")


class CertificateLogoForm(FlaskForm):
    order = fields.IntegerField()
    logo = fields.SelectField()


class GroupCertificateLogoForm(FlaskForm):
    certificate_logos = fields.FieldList(
        fields.FormField(CertificateLogoForm), validators=[validators.Optional()]
    )
