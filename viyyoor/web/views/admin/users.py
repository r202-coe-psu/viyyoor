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
    org_form = forms.accounts.UserSetting()
    organizations = models.Organization.objects()
    user = None
    org_form.organization.choices.extend([(str(org.id), org.name) for org in organizations])

    if user_id:
        user = models.User.objects(id=user_id).first()
        form = forms.accounts.UserForm(obj=user)
        org_form = forms.accounts.UserSetting(obj=user.user_setting)
        org_form.organization.choices.extend([(str(org.id), org.name) for org in organizations])
        if request.method == "GET" and user.user_setting.organization:
            org_form.organization.data = user.dashuser_settingboard_setting.organization
    
    if not form.validate_on_submit():
        return render_template(
            "/admin/users/add_or_edit.html",
            user=user,
            form=form,
            org_form=org_form,
        )

    if not user:
        user = models.User()


    form.populate_obj(user)
    org_form.populate_obj(user.dashboard_setting)
    if org_form.organization.data != "-":
        user.dashboard_setting.organization = models.Organization.objects.get(
            id=org_form.organization.data
            )
    else:
        user.dashboard_setting.organization = None

    user.dashboard_setting.updated_date = datetime.datetime.now()
    user.save()

    return redirect(url_for("admin.users.index"))
