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

from .. import models

module = Blueprint(
    "certificates",
    __name__,
    url_prefix="/certificate",
)


@module.route("/<certificate_id>")
def view(certificate_id):
    certificate = models.Certificate.objects(
        id=certificate_id, status="active", privacy="public"
    ).first()
    if not certificate:
        response = Response()
        response.status_code = 404
        return response

    class_ = certificate.class_
    participant_id = certificate.participant_id
    return render_template(
        "/certificates/view.html", class_=class_, participant_id=participant_id
    )
