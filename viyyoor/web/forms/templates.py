from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm, file
from wtforms import fields, widgets

import datetime

from .fields import TagListField, TextListField

from viyyoor import models

BaseTemplateForm = model_form(
    models.Class,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "last_updated_by",
        "status",
        'file',
    ],
    field_args={
        "name": {"label": "Name"},
        "description": {"label": "Desctiption"},
    },
)


class TemplateForm(BaseTemplateForm):
    tags = TagListField("Tags")
    template_file = file.FileField('Template File',
            validators=[file.FileRequired()]
            )

