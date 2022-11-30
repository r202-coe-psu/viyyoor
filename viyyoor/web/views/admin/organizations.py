from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    send_file,
    Response,
)
from flask_login import current_user, login_required

import datetime

from viyyoor.web import acl, forms
from viyyoor import models


module = Blueprint("organizations", __name__, url_prefix="/organizations")


@module.route("/")
def index():

    # organizations = []
    organizations = models.Organization.objects(
        status="active",
    )

    # for o in all_organizations:
    #     for a in o.admins:
    #         if a.user == current_user:
    #             organizations.append(o)

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
@acl.roles_required("admin")
def create_or_edit(organization_id):
    form = forms.organizations.OrganizationForm()
    organization = None

    if organization_id:
        organization = models.Organization.objects.get(id=organization_id)
        form = forms.organizations.OrganizationForm(obj=organization)

    if not form.validate_on_submit():

        return render_template(
            "/admin/organizations/create-edit.html",
            organization=organization,
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


@module.route("/<organization_id>/delete")
@acl.roles_required("admin")
def delete(organization_id):
    organization = models.Organization.objects.get(
        id=organization_id,
    )
    organization.status = "inactive"
    organization.save()

    return redirect(url_for("admin.organizations.index"))


@module.route("/<organization_id>")
@acl.roles_required("admin")
def view(organization_id):
    organization = models.Organization.objects.get(
        id=organization_id,
        status="active",
    )
    logos = models.CertificateLogo.objects(organization=organization)
    classes = models.Class.objects(organization=organization, status="active")
    return render_template(
        "/admin/organizations/view.html",
        logos=logos,
        organization=organization,
        classes=classes,
    )


