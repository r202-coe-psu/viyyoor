from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm

from viyyoor import models

BaseDashboardSettingForm = model_form(
    models.users.DashboardSetting,
    FlaskForm,
    exclude=["updated_date"],
    field_args={
        "organization": {"label": "Organization", "label_modifier": lambda o: o.name},
    },
)


class DashboardSetting(BaseDashboardSettingForm):
    pass
