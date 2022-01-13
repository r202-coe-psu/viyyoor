from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms


module = Blueprint("digital_certificates", __name__, url_prefix="/digital-certificates")


@module.route("")
def index():
    digital_certificates = models.DigitalCertificate.objects()
    return render_template(
        "/admin/digital_certificates/index.html",
        digital_certificates=digital_certificates,
    )


@module.route("/add", methods=["GET", "POST"])
def add():

    form = forms.digital_certificates.DigitalCertificateForm()
    if not form.validate_on_submit():
        return render_template(
            "/admin/digital_certificates/add.html",
            form=form,
        )

    ds = models.DigitalSignature(
        owner=current_user._get_current_object(),
        ip_address=request.remote_addr,
    )
    ds.file.put(
        form.digital_signature_file.data,
        filename=form.digital_signature_file.data.filename,
        content_type=form.digital_signature_file.data.content_type,
    )

    ds.encrypt_password(form.password.data)

    ds.save()

    return redirect(url_for("admin.digital_certificates.index"))
