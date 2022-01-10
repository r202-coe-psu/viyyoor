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
from jinja2 import Environment, PackageLoader, select_autoescape, Template

import io
import cairosvg
import qrcode
import base64

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

    data = certificate_template.template.file.read().decode()
    template = Template(data)

    text = [t.strip() for t in certificate_template.appreciate_text.split("\n")]

    appreciate_text = []
    if len(text) > 0:
        appreciate_text = [f"<tspan>{text[0]}</tspan>"]
        appreciate_text.extend(
            [f'<tspan x="50%" dy="10">{t.strip()}</tspan>' for t in text[1:]]
        )

    certificate = models.Certificate.objects(
        class_=class_, participant_id=participant_id
    ).first()
    validation_url = ""
    if certificate:
        validation_url = request.host_url[:-1] + url_for(
            "certificates.view", certificate_id=certificate.id
        )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=5,
        border=2,
    )
    qr.add_data(validation_url)
    qr.make(fit=True)

    qrcode_image = qr.make_image().convert("RGB")

    qrcode_io = io.BytesIO()
    qrcode_image.save(qrcode_io, "PNG", quality=100)
    qrcode_encoded = base64.b64encode(qrcode_io.getvalue()).decode("ascii")

    variables = dict(
        certificate_name=certificate_template.name,
        participant_name=(
            f"{participant.title} {participant.first_name} {participant.last_name}"
        ).strip(),
        appreciate_text="".join(appreciate_text),
        module_name=class_.name,
        issued_date=class_.issued_date.strftime("%B %Y, %-d"),
        validation_url=validation_url,
        validation_qrcode=f"image/png;base64,{qrcode_encoded}",
    )

    for endorser in class_.endorsers:
        variables[f"{ endorser.endorser_id }_name"] = (
            f"{endorser.title} { endorser.first_name } { endorser.last_name }"
        ).strip()

        text = [t.strip() for t in endorser.position.split("\n")]
        for i, t in enumerate(text):
            variables[f"{ endorser.endorser_id }_position_{i}"] = t

        signature = models.Signature.objects(owner=endorser.user).first()
        sign_encoded = ""
        if signature:
            sign_encoded = base64.b64encode(signature.file.read()).decode("ascii")
        variables[f"{ endorser.endorser_id }_sign"] = f"image/png;base64,{sign_encoded}"

    data = template.render(**variables)

    if extension == "png":
        output = cairosvg.svg2png(bytestring=data.encode())
        mimetype = "image/png"
    elif extension == "pdf":
        output = cairosvg.svg2pdf(bytestring=data.encode())
        mimetype = "application/pdf"

    image_io = io.BytesIO()
    image_io.write(output)
    image_io.seek(0)
    response = send_file(
        image_io,
        attachment_filename=f"{class_.id}-{participant_id}.{extension}",
        # as_attachment=True,
        mimetype=mimetype,
    )

    return response
