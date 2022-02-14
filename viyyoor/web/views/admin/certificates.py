from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("certificates", __name__, url_prefix="/certificates")


@module.route("/")
@acl.roles_required("admin")
def index():
    classes = models.Certificate.objects().distinct(field="class_")

    classes.sort(key=lambda c: c.id, reverse=True)
    certificate_stat = {}
    for class_ in classes:
        certificate_stat[str(class_.id)] = models.Certificate.objects(
            class_=class_
        ).count()

    return render_template(
        "/admin/certificates/index.html",
        classes=classes,
        certificate_stat=certificate_stat,
    )


@module.route("/classes/<class_id>")
@acl.roles_required("admin")
def view_in_class(class_id):
    class_ = models.Class.objects.get(id=class_id)
    certificates = models.Certificate.objects(class_=class_).exclude("file")

    return render_template(
        "/admin/certificates/view.html",
        certificates=certificates,
    )


@module.route("/<certificate_id>/delete")
@acl.roles_required("admin")
def delete(certificate_id):
    certificate = models.Certificate.objects.get(id=certificate_id)
    certificate.file.delete()
    certificate.delete()

    return redirect(url_for("admin.certificates.index"))
