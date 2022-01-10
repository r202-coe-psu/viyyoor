from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("classes", __name__, url_prefix="/classes")


@module.route("/")
@acl.roles_required("admin")
def index():
    classes = models.Class.objects(status="active")
    return render_template(
        "/admin/classes/index.html",
        classes=classes,
    )


@module.route(
    "/create",
    methods=["GET", "POST"],
    defaults={"class_id": None},
)
@module.route("/<class_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(class_id):
    form = forms.classes.ClassForm()
    class_ = None
    if class_id:
        class_ = models.Class.objects.get(id=class_id)
        form = forms.classes.ClassForm(obj=class_)

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/create-edit.html",
            form=form,
        )

    if not class_id:
        class_ = models.Class()
        class_.owner = current_user._get_current_object()

    form.populate_obj(class_)
    class_.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>")
@acl.roles_required("admin")
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template(
        "/admin/classes/view.html",
        class_=class_,
    )


@module.route("/<class_id>/delete")
@acl.roles_required("admin")
def delete(class_id):
    class_ = models.Class.objects.get(id=class_id)
    class_.status = "delete"
    class_.save()

    return redirect(url_for("admin.classes.index"))


@module.route(
    "/<class_id>/endorsers/add",
    methods=["GET", "POST"],
    defaults={"endorser_id": None},
)
@module.route("/<class_id>/endorsers/<endorser_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_or_edit_endorser(class_id, endorser_id):
    form = forms.classes.EndorserForm()
    endorser = None
    class_ = models.Class.objects.get(id=class_id)

    if endorser_id:
        endorser = class_.get_endorser(endorser_id)
        form = forms.classes.EndorserForm(obj=endorser)

    users = models.User.objects(roles="endorser").order_by("first_name")
    form.user.choices = [
        (str(user.id), f"{user.first_name} {user.last_name}") for user in users
    ]

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/add-or-edit-endorser.html",
            form=form,
            class_=class_,
        )

    endorser = class_.get_endorser(form.endorser_id.data)

    if not endorser:
        endorser = models.Endorser(endorser_id=form.endorser_id.data)
        class_.endorsers.append(endorser)

    form.populate_obj(endorser)
    endorser.user = models.User.objects.get(id=form.user.data)
    endorser.last_updated_by = current_user._get_current_object()
    class_.save()

    return redirect(url_for("admin.classes.add_or_edit_endorser", class_id=class_.id))


@module.route("/<class_id>/endorsers/<endorser_id>/delete", methods=["GET", "POST"])
@acl.roles_required("admin")
def delete_endorser(class_id, endorser_id):
    class_ = models.Class.objects.get(id=class_id)

    endorser = class_.get_endorser(endorser_id)

    if endorser:
        class_.endorsers.remove(endorser)
        class_.save()

    return redirect(url_for("admin.classes.add_or_edit_endorsers", class_id=class_.id))


@module.route(
    "/<class_id>/participants/add",
    methods=["GET", "POST"],
    defaults={"participant_id": ""},
)
@module.route("/<class_id>/participants/<participant_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_or_edit_participant(class_id, participant_id):
    class_ = models.Class.objects.get(id=class_id)

    form = forms.classes.ParticipantForm()
    participant = class_.get_participant(participant_id)
    if participant:
        form = forms.classes.ParticipantForm(obj=participant)

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/add-or-edit-participant.html",
            form=form,
            class_=class_,
        )

    if not participant:
        participant = class_.get_participant(participant_id)

    if not participant:
        participant = models.Participant()
        class_.participants.append(participant)

    form.populate_obj(participant)
    participant.last_updated_by = current_user._get_current_object()
    class_.save()

    return redirect(
        url_for("admin.classes.add_or_edit_participant", class_id=class_.id)
    )


@module.route("/<class_id>/participants/<participant_id>/delete")
@acl.roles_required("admin")
def delete_participant(class_id, participant_id):
    class_ = models.Class.objects.get(id=class_id)

    participant = class_.get_participant(participant_id)

    if participant:
        class_.participants.remove(participant)
        class_.save()

    return redirect(
        url_for("admin.classes.add_or_edit_participant", class_id=class_.id)
    )


@module.route(
    "/<class_id>/certificate_templates/add",
    methods=["GET", "POST"],
    defaults={"certificate_template_id": ""},
)
@module.route(
    "/<class_id>/certificate_templates/<certificate_template_id>/edit",
    methods=["GET", "POST"],
)
@acl.roles_required("admin")
def add_or_edit_certificate_template(class_id, certificate_template_id):
    class_ = models.Class.objects.get(id=class_id)

    form = forms.classes.CertificateTemplateForm()
    templates = models.Template.objects(status="active")
    certificate_template = class_.certificate_templates.get(certificate_template_id)

    if certificate_template_id:
        form = forms.classes.CertificateTemplateForm(obj=certificate_template)

    form.template.choices = [(str(t.id), t.name) for t in templates]

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/add-or-edit-certificate-template.html",
            form=form,
            class_=class_,
        )

    if not certificate_template:
        certificate_template = models.CertificateTemplate()
        class_.certificate_templates[form.group.data] = certificate_template

    if certificate_template_id:
        if certificate_template_id != form.group.data:
            class_.certificate_templates[form.group.data] = certificate_template
            class_.certificate_templates.pop(certificate_template_id)

    form.populate_obj(certificate_template)
    certificate_template.template = models.Template.objects.get(id=form.template.data)
    certificate_template.last_updated_by = current_user._get_current_object()
    class_.save()

    return redirect(
        url_for("admin.classes.add_or_edit_certificate_template", class_id=class_.id)
    )


@module.route("/<class_id>/certificate_templates/<certificate_template_id>/delete")
@acl.roles_required("admin")
def delete_certificate_template(class_id, certificate_template_id):
    class_ = models.Class.objects.get(id=class_id)

    if certificate_template_id in class_.certificate_templates:
        class_.certificate_templates.pop(certificate_template_id)
        class_.save()

    return redirect(
        url_for("admin.classes.add_or_edit_certificate_template", class_id=class_.id)
    )


@module.route("/<class_id>/release_certificate")
@acl.roles_required("admin")
def release_certificate(class_id):
    class_ = models.Class.objects.get(id=class_id)
    models.Certificate.objects(class_=class_, status="active").update(
        status="purge",
        last_updated_by=current_user._get_current_object(),
        updated_date=datetime.datetime.now(),
    )

    for participant in class_.participants:
        certificate = models.Certificate.objects(
            class_=class_, participant_id=participant.participant_id
        ).first()
        if not certificate:
            certificate = models.Certificate(
                class_=class_,
                participant_id=participant.participant_id,
                issuer=current_user._get_current_object(),
            )

        certificate.last_updated_by = current_user._get_current_object()
        certificate.updated_date = datetime.datetime.now()
        certificate.status = "active"
        certificate.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))
