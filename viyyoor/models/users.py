import mongoengine as me
import datetime

from flask_login import UserMixin
from flask import url_for


class User(me.Document, UserMixin):
    meta = {"collection": "users", "strict": False}
    username = me.StringField(required=True, unique=True, max_length=100)
    citizen_id = me.StringField(max_length=13)
    other_ids = me.ListField(me.StringField())

    title = me.StringField(max_length=50)
    email = me.StringField(required=True, unique=True, max_length=200)
    first_name = me.StringField(required=True, max_length=200)
    last_name = me.StringField(required=True, max_length=200)

    title_th = me.StringField(max_length=50)
    first_name_th = me.StringField(max_length=200)
    last_name_th = me.StringField(max_length=200)

    biography = me.StringField()

    picture = me.ImageField(thumbnail_size=(800, 600, True))

    status = me.StringField(required=True, default="disactive", max_length=15)
    roles = me.ListField(me.StringField(), default=["user"])

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    last_login_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    resources = me.DictField()

    def has_roles(self, roles):
        for role in roles:
            if role in self.roles:
                return True
        return False

    def get_picture(self):
        if self.picture:
            return url_for(
                "accounts.picture", user_id=self.id, filename=self.picture.filename
            )
        if "google" in self.resources:
            return self.resources["google"].get("picture", "")
        return url_for("static", filename="images/user.png")

    def get_signatures(self):
        from .signatures import Signature

        return Signature.objects(owner=self).order_by("-id")

    def get_signature(self):
        from .signatures import Signature

        return Signature.objects(owner=self).order_by("-id").first()
