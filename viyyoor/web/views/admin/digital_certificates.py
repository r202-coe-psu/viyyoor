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
@acl.roles_required("admin")
def index():
    digital_certificates = models.DigitalCertificate.objects().order_by("-id")
    return render_template(
        "/admin/digital_certificates/index.html",
        digital_certificates=digital_certificates,
    )


@module.route(
    "/add", methods=["GET", "POST"], defaults=dict(digital_certificate_id=None)
)
@module.route("/<digital_certificate_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_or_edit(digital_certificate_id):
    form = forms.digital_certificates.DigitalCertificateForm()

    digital_certificate = None
    if digital_certificate_id:
        digital_certificate = models.DigitalCertificate.objects.get(
            id=digital_certificate_id
        )

    if digital_certificate and request.method == "GET":
        form = forms.digital_certificates.DigitalCertificateForm(
            obj=digital_certificate
        )

        if digital_certificate.type_ == "self":
            if digital_certificate.password:
                form.password.data = digital_certificate.decrypt_password(
                    digital_certificate.password
                ).decode()
        elif digital_certificate.type_ == "psusigner":
            if digital_certificate.signer_api.secret:
                form.signer_api.secret.data = digital_certificate.decrypt_password(
                    digital_certificate.signer_api.secret
                ).decode()
            if digital_certificate.signer_api.agent_key:
                form.signer_api.agent_key.data = digital_certificate.decrypt_password(
                    digital_certificate.signer_api.agent_key
                ).decode()
            if digital_certificate.signer_api.jwt_secret:
                form.signer_api.jwt_secret.data = digital_certificate.decrypt_password(
                    digital_certificate.signer_api.jwt_secret
                ).decode()

    if not form.validate_on_submit():
        return render_template(
            "/admin/digital_certificates/add.html",
            form=form,
        )

    if not digital_certificate:
        digital_certificate = models.DigitalCertificate(
            owner=current_user._get_current_object(),
            type_=form.type_.data,
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
            expired_date=datetime.datetime.now() + datetime.timedelta(days=365 * 100),
        )

    digital_certificate.type_ = form.type_.data

    if form.type_.data == "self":
        if form.digital_certificate_file.data:
            certificate_data = form.digital_certificate_file.data.read()

            key, cert, _ = pkcs12.load_key_and_certificates(
                certificate_data,
                form.password.data.encode(),
                backends.default_backend(),
            )

            digital_certificate.issuer = cert.issuer.get_attributes_for_oid(
                NameOID.COMMON_NAME
            )[0].value
            digital_certificate.subject = cert.subject.get_attributes_for_oid(
                NameOID.COMMON_NAME
            )[0].value
            digital_certificate.started_date = cert.not_valid_before
            digital_certificate.expired_date = cert.not_valid_after

            form.digital_certificate_file.data.seek(0)
            digital_certificate.file.put(
                form.digital_certificate_file.data,
                filename=form.digital_certificate_file.data.filename,
                content_type=form.digital_certificate_file.data.content_type,
            )

        if form.password.data:
            encrypted_password = digital_certificate.encrypt_password(
                form.password.data
            )
            digital_certificate.password = encrypted_password

        digital_certificate.ca_download_url = form.ca_download_url.data
    elif form.type_.data == "psusigner":
        digital_certificate.signer_api.code = form.signer_api.code.data
        digital_certificate.signer_api.api_url = form.signer_api.api_url.data
        digital_certificate.signer_api.secret = digital_certificate.encrypt_password(
            form.signer_api.secret.data
        )
        digital_certificate.signer_api.agent_key = digital_certificate.encrypt_password(
            form.signer_api.agent_key.data
        )
        digital_certificate.signer_api.jwt_secret = (
            digital_certificate.encrypt_password(form.signer_api.jwt_secret.data)
        )

    digital_certificate.updated_by = current_user._get_current_object()

    digital_certificate.save()

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
