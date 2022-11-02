from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm, file
from wtforms import fields, widgets, validators

import datetime

from .fields import TagListField, TextListField

from viyyoor import models

BaseTemplateForm = model_form(
    models.Template,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "last_updated_by",
        "owner",
        "status",
        "file",
        "control",
    ],
    field_args={
        "name": {
            "label": "Name",
        },
        "description": {
            "label": "Desctiption",
        },
    },
)


class TemplateForm(BaseTemplateForm):
    tags = TagListField("Tags")
    template_file = file.FileField(
        "Template File",
        validators=[
            file.FileAllowed(["svg"], "รับเฉพาะไฟล์ svg เท่านั้น"),
        ],
    )
    thumbnail_file = file.FileField(
        "Thumbnail File",
        validators=[
            file.FileAllowed(["png", "jpg"], "รับเฉพาะไฟล์ png เเละ jpg เท่านั้น"),
        ],
    )


BaseControlTemplateForm = model_form(
    models.Control,
    FlaskForm,
    only=["status"],
    field_args={
        "status": {"label": "Status"},
    },
)


class ControlTemplateForm(BaseControlTemplateForm):
    organizations = fields.SelectMultipleField()


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
    classes = fields.SelectField("Class", validators=[validators.InputRequired()])
