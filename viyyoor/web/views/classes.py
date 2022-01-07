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
import cairosvg


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


@module.route("/<class_id>/certificate/<participant_id>.svg")
# @login_required
def generate_certificate(class_id, participant_id):
    response = Response()
    response.status_code = 404

    class_ = models.Class.objects.get(id=class_id)
    participant = class_.get_participant(participant_id)
    certificate_template = class_.certificate_templates.get(participant.group)

    from jinja2 import Environment, PackageLoader, select_autoescape, Template

    if not certificate_template.template:
        return response

    data = certificate_template.template.file.read().decode()
    template = Template(data)

    text = [t.strip() for t in certificate_template.appreciate_text.split("\n")]

    appreciate_text = []
    if len(text) > 0:
        appreciate_text = [f"<tspan>{text[0]}</tspan>"]
        appreciate_text.extend(
            [f'<tspan x="50%" dy="10">{t.strip()}</tspan>' for t in text[1:]]
        )

    certificate_url = url_for(
        "certificates.view", class_id=class_id, participant_id=participant_id
    )
    variables = dict(
        certificate_name=certificate_template.name,
        participant_name=f"{participant.first_name} {participant.last_name}",
        appreciate_text="".join(appreciate_text),
        module_name=class_.name,
        issued_date=class_.issued_date.strftime("%B %Y, %-d"),
        validation_url=f"{request.host_url}{certificate_url}",
    )

    for endorser in class_.endorsers:
        variables[
            f"{ endorser.endorser_id }_name"
        ] = f"{ endorser.user.first_name } { endorser.user.last_name }"

        text = [t.strip() for t in endorser.position.split("\n")]
        position = []
        if len(text) > 0:
            position = [f"<tspan>{text[0]}</tspan>"]
            position.extend([f'<tspan x="50%" dy="5">{t}</tspan>' for t in text[1:]])

        variables[f"{ endorser.endorser_id }_position"] = "".join(position)

    data = template.render(**variables)

    image_io = io.BytesIO()
    image_io.write(data.encode())
    image_io.seek(0)
    response = send_file(
        image_io,
        attachment_filename=f"{class_.id}-{participant_id}.svg",
        # as_attachment=True,
        mimetype=certificate_template.template.file.content_type,
    )

    return response
