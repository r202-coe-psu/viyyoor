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


from .. import models

module = Blueprint(
    "classes",
    __name__,
    url_prefix="/classes",
)


@module.route("/")
@login_required
def index():
    enrollments = models.Enrollment.objects(user=current_user._get_current_object())
    return render_template("/classes/index.html", enrollments=enrollments)


@module.route("/<class_id>")
@login_required
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    enrollment = models.Enrollment.objects(
        user=current_user._get_current_object(), enrolled_class=class_
    ).first()
    return render_template("/classes/view.html", enrollment=enrollment, class_=class_)


@module.route("/<class_id>/enroll")
@login_required
def enroll(class_id):
    class_ = models.Class.objects.get(id=class_id)
    enrollment = models.Enrollment.objects(
        user=current_user._get_current_object(), enrolled_class=class_
    ).first()
    if not enrollment:
        enrollment = models.Enrollment(
            user=current_user._get_current_object(), enrolled_class=class_
        )
        enrollment.save()
        class_.enrollments.append(enrollment)
        class_.save()

    return redirect(url_for("classes.view", class_id=class_.id))


@module.route("/<class_id>/certificate/<participant_id>.<extension>")
# @login_required
def render_certificate(class_id, participant_id, extension):
    response = Response()
    response.status_code = 404

    class_ = models.Class.objects.get(id=class_id)
    participant = class_.get_participant(participant_id)
    certificate_template = class_.certificate_templates.get(participant.group)

    if not certificate_template:
        return response

    image_io = class_.render_certificate(participant_id, extension)

    if extension == "png":
        mimetype = "image/png"
    elif extension == "pdf":
        mimetype = "application/pdf"

    response = send_file(
        image_io,
        attachment_filename=f"{class_.id}-{participant_id}.{extension}",
        # as_attachment=True,
        mimetype=mimetype,
    )

    return response
