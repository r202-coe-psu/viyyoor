from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
)
from flask_login import current_user, login_required

import datetime

from viyyoor.web import forms
from viyyoor import models


module = Blueprint("organizations", __name__, url_prefix="/organizations")


@module.route("/")
@login_required
def index():
    if current_user.has_roles(["superadmin"]):
        organizations = models.Organization.objects(
            status="active",
        )
    else:
        organizations = models.Organization.objects(
            created_by=current_user._get_current_object(),
            status="active",
        )
    return render_template(
        "/admin/organizations/index.html",
        now=datetime.datetime.now,
        organizations=organizations,
    )


@module.route(
    "/create",
    methods=["GET", "POST"],
    defaults={"organization_id": None},
)
@module.route("/<organization_id>/edit", methods=["GET", "POST"])
@login_required
def create_or_edit(organization_id):
    form = forms.organizations.OrganizationForm()
    organization = None

    if organization_id:
        organization = models.organizations.Organization.objects.get(
            id=organization_id,
        )
        form = forms.organizations.OrganizationForm(
            obj=organization,
        )

    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/create-edit.html",
            form=form,
        )

    if not organization_id:
        organization = models.Organization()
        organization.created_by = current_user._get_current_object()

    form.populate_obj(organization)

    organization.last_updated_by = current_user._get_current_object()
    organization.last_updated_date = datetime.datetime.now()

    organization.save()

    return redirect(url_for("admin.organizations.index"))


@module.route("/<organization_id>")
@login_required
def view(organization_id):
    organization = models.Organization.objects.get(
        id=organization_id,
        status="active",
    )
    return render_template(
        "/admin/organizations/view.html",
        organization=organization,
    )


@module.route("/<organization_id>/delete")
@login_required
def delete(organization_id):
    organization = models.Organization.objects.get(
        id=organization_id,
    )
    organization.status = "inactive"
    organization.save()

    return redirect(url_for("admin.organizations.index"))
