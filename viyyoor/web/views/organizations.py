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
    organizations = models.Organization.objects(
        status="active",
    )
    return render_template(
        "/admin/organizations/index.html",
        now=datetime.datetime.now,
        organizations=organizations,
    )


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


@module.route("/<organization_id>/edit", methods=["GET", "POST"])
@login_required
def edit(organization_id):
    organization = models.Organization.objects.get(id=organization_id)
    form = forms.organizations.AdminOrganizationEditForm()

    if not form.validate_on_submit():
        form.name.data = organization.name
        form.description.data = organization.description
        return render_template(
            "/organizations/edit.html", organization=organization, form=form
        )

    form.populate_obj(organization)
    organization.save()

    return redirect(url_for("organizations.view", organization_id=organization_id))


@module.route("/logos/<logo_id>/download/<filename>")
def download_logo(logo_id, filename):
    response = Response()
    response.status_code = 404
    logo = models.CertificateLogo.objects.get(id=logo_id)

    if logo:
        response = send_file(
            logo.logo_file,
            download_name=filename,
            mimetype=logo.logo_file.content_type,
        )

    return response


@module.route(
    "/<organization_id>/logos/<logo_id>/set_as_organization_logo", methods=["POST"]
)
def change_organization_logo(organization_id, logo_id):
    organization = models.Organization.objects.get(id=organization_id)
    old_logo = models.CertificateLogo.objects(
        organization=organization, marked_as_organization_logo=True
    ).first()
    if old_logo:
        old_logo.marked_as_organization_logo = False
        old_logo.last_updated_by = current_user._get_current_object()
        old_logo.updated_date = datetime.datetime.now()
        old_logo.save()

    new_logo = models.CertificateLogo.objects.get(id=logo_id)
    new_logo.marked_as_organization_logo = True
    new_logo.last_updated_by = current_user._get_current_object()
    new_logo.updated_date = datetime.datetime.now()
    new_logo.save()

    return redirect(url_for("organizations.view", organization_id=organization.id))


@module.route(
    "/<organization_id>/users/<organization_user_id>/<operator>",
    methods=["GET", "POST"],
)
def manage_organization_user(organization_id, organization_user_id, operator):
    organization = models.Organization.objects.get(id=organization_id)
    organization_user = models.OrganizationUserRole.objects.get(id=organization_user_id)

    if operator == "deactivate":
        organization_user.status = "disactive"
    elif operator == "activate":
        organization_user.status = "active"

    organization_user.last_modifier = current_user._get_current_object()
    organization_user.updated_date = datetime.datetime.now()
    organization_user.last_ip_address = request.headers.get(
        "X-Forwarded-For", request.remote_addr
    )
    organization_user.save()

    print(operator, "user", organization_user.user.first_name)
    return redirect(
        url_for(
            "admin.organizations.view_users",
            organization_id=organization.id,
            role="all",
        )
    )
