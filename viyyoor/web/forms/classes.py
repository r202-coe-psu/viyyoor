from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm
from wtforms import fields, widgets

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
        "endorses",
        "status",
    ],
    field_args={
        "name": {"label": "Name"},
        "description": {"label": "Desctiption"},
        "started_date": {"label": "Start Date"},
        "ended_date": {"label": "End Date"},
    },
)


class ClassForm(BaseClassForm):
    tags = TagListField("Tags")
    started_date = fields.DateField(
        "Started Date",
        format="%Y-%m-%d",
        widget=widgets.TextInput(),
        default=datetime.datetime.today,
    )
    ended_date = fields.DateField(
        "Ended Date",
        format="%Y-%m-%d",
        widget=widgets.TextInput(),
        default=datetime.datetime.today,
    )


BaseEndorserForm = model_form(
    models.Endorser,
    FlaskForm,
    exclude=[
        "user",
        "updated_date",
    ],
    field_args={"position": {"label": "Position"}},
)


class EndorserForm(BaseEndorserForm):
    user = fields.SelectField()


class EndorserGrantForm(FlaskForm):
    users = fields.SelectMultipleField()


class ParticipantForm(FlaskForm):
    pass
