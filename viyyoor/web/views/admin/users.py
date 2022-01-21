from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("users", __name__, url_prefix="/users")


@module.route("/")
@acl.roles_required("admin")
def index():
    form = forms.accounts.UserForm()
    users = models.User.objects().order_by("-id")
    return render_template(
        "/admin/users/index.html",
        users=users,
        form=form,
    )


@module.route("/add", methods=["POST", "GET"], defaults={"user_id": None})
@module.route("/<user_id>/edit", methods=["POST", "GET"])
@acl.roles_required("admin")
def add_or_edit(user_id):
    form = forms.accounts.UserForm()
    user = None
    if user_id:
        user = models.User.objects(id=user_id).first()
        form = forms.accounts.UserForm(obj=user)

    if not form.validate_on_submit():
        return render_template(
            "/admin/users/add_or_edit.html",
            user=user,
            form=form,
        )

    if not user:
        user = models.User()

    form.populate_obj(user)

    user.save()

    return redirect(url_for("admin.users.index"))
