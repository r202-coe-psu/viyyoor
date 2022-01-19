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
import datetime

from viyyoor import models
from .. import forms
from .. import acl

from .digital_signatures import sign_digital_signature

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
    if "admin" in current_user.roles or "endorse" in current_user.roles:
        return render_template("/classes/view_endorse.html", class_=class_)

    return render_template("/classes/view.html", class_=class_)


@module.route("/<class_id>/endorse", methods=["GET", "POST"])
@acl.roles_required("endorser")
def endorse(class_id):

    class_ = models.Class.objects.get(id=class_id)
    # certificates = models.Certificate.objects(class_=class_, status="prerelease")
    # form = forms.classes.EndorsementForm()
    # if not form.validate_on_submit():
    #     return render_template(
    #         "/classes/endorse.html", form=form, class_=class_, certificates=certificates
    #     )

    certificates = models.Certificate.objects(class_=class_, status="prerelease")

    endorsers = class_.get_endorsers_by_user(current_user._get_current_object())
    if not len(endorsers):
        return redirect(url_for("dashboard.index"))

    for certificate in certificates:
        # sign signature hear1
        # sign_digital_signature(user, certificate, password)
        endorsement = models.Endorsement(
            endorser=current_user._get_current_object(),
            ip_address=request.remote_addr,
        )

        for endorser in endorsers:
            certificate.endorsements[endorser.endorser_id] = endorsement

        check_approval = True
        for key, endorser in class_.endorsers.items():
            if endorser.endorser_id not in certificate.endorsements:
                check_approval = False
            elif (
                endorser.endorser_id in certificate.endorsements
                and endorser.user
                != certificate.endorsements[endorser.endorser_id].endorser
            ):
                check_approval = False

            if not check_approval:
                break

        if check_approval:
            dc = (
                models.DigitalCertificate.objects(status="active")
                .order_by("-id")
                .first()
            )
            sign_digital_signature(certificate, dc)
            certificate.signed_date = datetime.datetime.now()
            certificate.status = "completed"
            certificate.privacy = "public"

        certificate.updated_date = datetime.datetime.now()
        certificate.save()

    return redirect(url_for("dashboard.index"))


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
