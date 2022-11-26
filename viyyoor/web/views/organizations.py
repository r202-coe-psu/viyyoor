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
    logos = models.CertificateLogo.objects()
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
