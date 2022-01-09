from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    Response,
)
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("signatures", __name__, url_prefix="/signatures")


@module.route("/")
@acl.roles_required("admin")
def index():
    signatures = models.Signature.objects(status="active")
    return render_template(
        "/admin/signatures/index.html",
        signatures=signatures,
    )


@module.route(
    "/create",
    methods=["GET", "POST"],
    defaults={"signature_id": ""},
)
@module.route("/<signature_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(signature_id):
    form = forms.signatures.SignatureForm()

    if signature_id:
        signature = models.Signature.objects.get(id=signature_id)
        form = forms.signatures.SignatureForm(obj=signature)

    endorsers = models.User.objects(roles="endorser")
    form.user.choices = [
        (str(user.id), f"{ user.first_name } { user.last_name }") for user in endorsers
    ]

    if not form.validate_on_submit():
        print(form.data)
        print(form.errors)
        return render_template(
            "/admin/signatures/create-edit.html",
            form=form,
        )

    if not signature_id:
        signature = models.Signature(
            last_updated_by=current_user._get_current_object(),
        )

    form.populate_obj(signature)

    signature.owner = models.User.objects.get(id=form.user.data)

    if not signature_id:
        signature.file.put(
            form.signature_file.data,
            filename=form.signature_file.data.filename,
            content_type=form.signature_file.data.content_type,
        )
    else:

        signature.file.replace(
            form.signature_file.data,
            filename=form.signature_file.data.filename,
            content_type=form.signature_file.data.content_type,
        )

    signature.save()

    return redirect(url_for("admin.signatures.index"))


@module.route("/<signature_id>")
@acl.roles_required("admin")
def view(signature_id):
    signature = models.Signature.objects.get(id=signature_id)
    return render_template(
        "/admin/signatures/view.html",
        signature=signature,
    )


@module.route("/<signature_id>/delete")
@acl.roles_required("admin")
def delete(signature_id):
    signature = models.Signature.objects.get(id=signature_id)
    signature.status = "delete"
    signature.save()

    return redirect(url_for("admin.signatures.index"))


@module.route("/<signature_id>/<filename>")
@acl.roles_required("admin")
def download(signature_id, filename):
    response = Response()
    response.status_code = 404

    signature = models.Signature.objects.get(id=signature_id)

    if signature:
        response = send_file(
            signature.file,
            attachment_filename=signature.file.filename,
            # as_attachment=True,
            mimetype=signature.file.content_type,
        )

    return response
