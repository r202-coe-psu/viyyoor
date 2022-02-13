from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("certificates", __name__, url_prefix="/certificates")


@module.route("/")
@acl.roles_required("admin")
def index():
    certificates = models.Certificate.objects
    return render_template(
        "/admin/certificates/index.html",
        certificates=certificates,
    )


@module.route("/<certificate_id>/delete")
@acl.roles_required("admin")
def delete(certificate_id):
    certificate = models.Certificate.objects.get(id=certificate_id)
    certificate.file.delete()
    certificate.delete()

    return redirect(url_for("admin.certificates.index"))
