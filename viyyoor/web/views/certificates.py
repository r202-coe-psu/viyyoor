from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    Response,
    send_file,
    request,
)
from flask_login import current_user, login_required
import io
from pdf2image import convert_from_bytes

from .. import models

module = Blueprint(
    "certificates",
    __name__,
    url_prefix="/certificates",
)


@module.route("/<certificate_id>")
def view(certificate_id):
    certificate = models.Certificate.objects(
        id=certificate_id, status="completed", privacy="public"
    ).first()

    if not certificate:
        if current_user.is_authenticated and (
            "admin" in current_user.roles or "endorser" in current_user.roles
        ):
            certificate = models.Certificate.objects(id=certificate_id).first()

    if not certificate:
        response = Response()
        response.status_code = 404
        return response

    class_ = certificate.class_
    participant_id = certificate.participant_id
    return render_template(
        "/certificates/view.html",
        class_=class_,
        participant_id=participant_id,
        certificate=certificate,
    )


@module.route(
    "/<certificate_id>/certificate.<extension>", defaults={"extension": "png"}
)
@module.route("/<certificate_id>/certificate.<extension>")
def download(certificate_id, extension):
    response = Response()
    response.status_code = 404

    certificate = models.Certificate.objects(
        id=certificate_id, status="completed", privacy="public"
    ).first()

    if not certificate:
        if current_user.is_authenticated and (
            "admin" in current_user.roles or "endorser" in current_user.roles
        ):
            certificate = models.Certificate.objects(id=certificate_id).first()

    if not certificate:
        return response

    class_ = certificate.class_
    participant = class_.get_participant(certificate.participant_id)

    if extension == "pdf":
        mimetype = "application/pdf"

        response = send_file(
            certificate.file,
            download_name=f"certificate-{ participant.name.replace(' ', '-') }.pdf",
            # as_attachment=True,
            mimetype=mimetype,
        )
    elif extension == "png":
        mimetype = "image.png"

        image = convert_from_bytes(certificate.file.read(), dpi=100)
        image_bytes = io.BytesIO()
        image[0].save(image_bytes, "png")
        image_bytes.seek(0)

        response = send_file(
            image_bytes,
            # class_.render_certificate(participant.id, extension),
            download_name=f"certificate-{ participant.name.replace(' ', '-') }.png",
            # as_attachment=True,
            mimetype=mimetype,
        )

    return response
