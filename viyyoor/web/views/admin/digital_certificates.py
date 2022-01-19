from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms


module = Blueprint("digital_certificates", __name__, url_prefix="/digital-certificates")


@module.route("")
def index():
    digital_certificates = models.DigitalCertificate.objects().order_by("-id")
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

    dc = models.DigitalCertificate(
        owner=current_user._get_current_object(),
        ip_address=request.remote_addr,
    )
    dc.file.put(
        form.digital_certificate_file.data,
        filename=form.digital_certificate_file.data.filename,
        content_type=form.digital_certificate_file.data.content_type,
    )

    encrypted_password = dc.encrypt_password(form.password.data)
    dc.password = encrypted_password
    dc.ca_download_url = form.ca_download_url.data

    dc.save()

    return redirect(url_for("admin.digital_certificates.index"))
