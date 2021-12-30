from flask import Blueprint, render_template, url_for, redirect, Response, send_file
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


@module.route("/<class_id>/certificate/<participant_id>.svg")
# @login_required
def view_certificate(class_id, participant_id):
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
    # print(template.render(the="variables", go="here"))

    variables = dict(
        certificate_name=certificate_template.name,
        participant_name=f"{participant.first_name} {participant.last_name}",
        certification_text=certificate_template.appreciate_text,
        module_name=class_.name,
        issued_date=class_.issued_date,
    )

    for endorser in class_.endorsers:
        variables[
            f"{ endorser.endorser_id }_name"
        ] = f"{ endorser.user.first_name } { endorser.user.last_name }"
        variables[f"{ endorser.endorser_id }_position"] = endorser.position

    print(variables)
    data = template.render(**variables)

    import io

    x = io.BytesIO()
    x.write(data.encode())
    x.seek(0)
    response = send_file(
        x,
        attachment_filename=f"{participant_id}.svg",
        # as_attachment=True,
        mimetype=certificate_template.template.file.content_type,
    )

    return response
