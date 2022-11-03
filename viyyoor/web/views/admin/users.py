from flask import Blueprint, render_template, redirect, url_for, request
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
    org_form = forms.accounts.UserSettingForm()
    organizations = models.Organization.objects().order_by("-id")
    user = None
    org_form.organizations.choices = [(str(o.id), o.name) for o in organizations]
    if user_id:
        user = models.User.objects(id=user_id).first()
        form = forms.accounts.UserForm(obj=user)
        org_form = forms.accounts.UserSettingForm(obj=user.user_setting)
        org_form.organizations.choices = [(str(o.id), o.name) for o in organizations]

    if not form.validate_on_submit():
        org_form.organizations.data = [
            str(o.id) for o in user.user_setting.organizations
        ]
        return render_template(
            "/admin/users/add_or_edit.html",
            user=user,
            form=form,
            org_form=org_form,
        )

    if not user:
        user = models.User()

    form.populate_obj(user)
    org_form.populate_obj(user.user_setting)

    user.user_setting.organizations = [
        models.Organization.objects.get(id=oid) for oid in org_form.organizations.data
    ]
    user.user_setting.updated_date = datetime.datetime.now()

    if not user.user_setting.current_organization:
        user.user_setting.current_organization = user.user_setting.organizations[0]

    if not user.user_setting.organizations:
        user.user_setting.current_organization = None

    user.save()

    return redirect(url_for("admin.users.index"))
