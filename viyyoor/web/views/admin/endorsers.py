from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("endorsers", __name__, url_prefix="/endorsers")


@module.route("/")
@acl.roles_required("admin")
def index():
    form = forms.classes.EndorserGrantForm()
    form.users.choices = [
        (str(user.id), f"{user.first_name} {user.last_name}")
        for user in models.User.objects(status="active")
    ]
    endorsers = models.User.objects(status="active", roles="endorser")
    return render_template(
        "/admin/endorsers/index.html",
        endorsers=endorsers,
        form=form,
    )


@module.route("/grant", methods=["POST"])
@acl.roles_required("admin")
def grant():
    form = forms.classes.EndorserGrantForm()
    form.users.choices = [
        (str(user.id), f"{user.first_name} {user.last_name}")
        for user in models.User.objects(status="active")
    ]

    if not form.validate_on_submit():
        return redirect(url_for("endorsers.index"))

    for user_id in form.users.data:
        user = models.User.objects.get(id=user_id)
        if "endorser" not in user.roles:
            user.roles.append("endorser")
            user.save()

    return redirect(url_for("admin.endorsers.index"))


@module.route("/<user_id>/delete")
@acl.roles_required("admin")
def delete(user_id):
    user = models.User.objects.get(id=user_id)
    user.roles.remove("endorser")
    user.save()

    return redirect(url_for("admin.endorsers.index"))
