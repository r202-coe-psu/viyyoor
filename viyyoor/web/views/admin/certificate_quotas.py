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


module = Blueprint("certificate_quotas", __name__, url_prefix="/certificate_quotas")


@module.route("/")
def index():
    certificate_quotas = models.CertificateQuota.objects()
    return render_template(
        "/admin/certificate_quota/index.html",
        now=datetime.datetime.now,
        certificate_quotas=certificate_quotas,
    )


@module.route("/<certificate_quota_id>")
@acl.organization_roles_required("admin", "endorser", "staff")
def view(certificate_quota_id):

    certificate_quotas = models.CertificateQuota.objects.get(
        id=certificate_quota_id,
    )

    return render_template(
        "/organizations/view.html",
        classes=classes,
    )


@module.route("/<organization_id>/edit", methods=["GET", "POST"])
@acl.organization_roles_required("admin")
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
