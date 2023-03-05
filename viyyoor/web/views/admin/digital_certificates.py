from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user

import datetime
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


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

    certificate_data = form.digital_certificate_file.data.read()

    key, cert, _ = pkcs12.load_key_and_certificates(
        certificate_data, form.password.data.encode(), backends.default_backend()
    )

    issuer = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    subject = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    started_date = cert.not_valid_before
    expired_date = cert.not_valid_after

    dc = models.DigitalCertificate(
        owner=current_user._get_current_object(),
        ip_address=request.remote_addr,
        issuer=issuer,
        subject=subject,
        started_date=started_date,
        expired_date=expired_date,
    )

    form.digital_certificate_file.data.seek(0)
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


@module.route("/<digital_certificate_id>/action/<action>")
@acl.roles_required("admin")
def action(digital_certificate_id, action):
    dc = models.DigitalCertificate.objects.get(id=digital_certificate_id)
    if action == "deactivate":
        dc.status = "inactive"
        dc.save()

    elif action == "activate":
        dc.status = "active"
        dc.save()

    return redirect(url_for("admin.digital_certificates.index"))
