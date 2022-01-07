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
)


@module.route("/<class_id>/<participant_id>")
def view(class_id, participant_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template(
        "/certificates/view.html", class_=class_, participant_id=participant_id
    )
