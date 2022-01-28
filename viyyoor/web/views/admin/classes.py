from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    request,
    Response,
)
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

from . import pdf_utils
import pandas
import xlsxwriter
import json
import io
from copy import deepcopy

module = Blueprint("classes", __name__, url_prefix="/classes")


@module.route("/")
@acl.roles_required("admin")
def index():
    classes = models.Class.objects(status="active").order_by("-id")
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


@module.route("/<class_id>/copy")
@acl.roles_required("admin")
def copy(class_id):
    class_ = models.Class.objects.get(id=class_id)
    if not class_:
        return redirect(url_for("admin.classes.index"))

    now = datetime.datetime.now()
    new_class = deepcopy(class_)
    new_class.id = None
    new_class.name = f"{ new_class.name } copy { now.strftime('%Y-%m-%d') }"
    new_class.participants = {}
    new_class.started_date = datetime.datetime.now()
    new_class.ended_data = datetime.datetime.now()
    new_class.issued_date = datetime.datetime.now()
    new_class.created_date = datetime.datetime.now()
    new_class.updated_date = datetime.datetime.now()
    new_class.owner = current_user._get_current_object()
    new_class.status = "active"
    new_class.save()

    return redirect(url_for("admin.classes.view", class_id=new_class.id))


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

    endorser = class_.get_endorser(endorser_id)

    if not endorser:
        endorser = models.Endorser(endorser_id=form.endorser_id.data)
    else:
        class_.endorsers.pop(endorser_id)

    class_.endorsers[form.endorser_id.data] = endorser

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
        class_.endorsers.pop(endorser_id)
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
        if request.method == "GET":
            if participant.extra:
                form.extra_data.data = json.dumps(participant.extra, ensure_ascii=False)

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/add-or-edit-participant.html",
            form=form,
            class_=class_,
        )

    if not participant:
        participant = models.Participant()
    else:
        class_.participants.pop(str(participant.id))

    class_.participants[str(participant.id)] = participant

    form.populate_obj(participant)
    if form.extra_data.data:
        participant.extra = json.loads(form.extra_data.data)
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
        certificate = models.Certificate.objects(
            class_=class_, participant_id=participant_id
        ).first()
        if certificate:
            certificate.status = "purge"
            certificate.save()

        class_.participants.pop(participant_id)
        class_.save()

    return redirect(
        url_for("admin.classes.add_or_edit_participant", class_id=class_.id)
    )


@module.route(
    "/<class_id>/participants/add-from-file",
    methods=["GET", "POST"],
)
@acl.roles_required("admin")
def add_participant_from_file(class_id):
    class_ = models.Class.objects.get(id=class_id)

    form = forms.classes.ParticipantFileForm()

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/add-participant-from-file.html",
            form=form,
            class_=class_,
        )

    dfs = pandas.read_excel(form.participant_file.data)
    dfs.columns = dfs.columns.str.lower()
    for index, row in dfs.iterrows():
        common_id = str(row["id"]).strip()
        participant = models.Participant(common_id=common_id)
        class_.participants[str(participant.id)] = participant

        if row["grade"] in ["A", "B+", "B", "C+", "C", "D+", "D", "E", "W"]:
            if row["grade"] in ["A", "B+", "B", "C+", "C"]:
                participant.group = "achievement"
            elif row["grade"] in ["D+", "D"]:
                participant.group = "participant"
            else:
                class_.participants.pop(pid)
                continue
        else:
            participant.group = row["grade"]

        participant.name = str(row["name"]).strip()
        participant.last_updated_by = current_user._get_current_object()
        participant.updated_date = datetime.datetime.now()
        participant.extra = row.to_dict()

    class_.save()

    # if not participant:
    #     participant = class_.get_participant(participant_id)

    # if not participant:
    #     participant = models.Participant()
    #     class_.participants.append(participant)

    # form.populate_obj(participant)
    # participant.last_updated_by = current_user._get_current_object()
    # class_.save()

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
        if request.method == "GET":
            form.template.data = str(certificate_template.template.id)

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


@module.route("/<class_id>/prepair_certificate")
@acl.roles_required("admin")
def prepare_certificate(class_id):
    class_ = models.Class.objects.get(id=class_id)
    models.Certificate.objects(class_=class_, status="prerelease").update(
        status="prepare",
        last_updated_by=current_user._get_current_object(),
        updated_date=datetime.datetime.now(),
    )

    for key, participant in class_.participants.items():
        certificate = models.Certificate.objects(
            class_=class_, participant_id=participant.id, status="prepare"
        ).first()

        if not certificate:
            certificate = models.Certificate(
                class_=class_,
                participant_id=participant.id,
                common_id=participant.common_id,
            )
            certificate.last_updated_by = current_user._get_current_object()
            certificate.issuer = current_user._get_current_object()
            certificate.save()
            certificate.file.put(class_.render_certificate(participant.id, "pdf"))

        else:
            certificate.file.replace(class_.render_certificate(participant.id, "pdf"))

        certificate.updated_date = datetime.datetime.now()
        certificate.issued_date = class_.issued_date
        certificate.last_updated_by = current_user._get_current_object()
        certificate.issuer = current_user._get_current_object()
        certificate.status = "prerelease"
        certificate.privacy = "prerelease"
        certificate.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/rebuild_certificate")
@acl.roles_required("admin")
def rebuild_certificate(class_id):
    class_ = models.Class.objects.get(id=class_id)

    certificate_id = request.args.get("certificate_id", None)

    query = None
    if certificate_id:
        query = models.Certificate.objects(id=certificate_id, class_=class_)
    else:
        query = models.Certificate.objects(class_=class_)

    if query:
        query.update(
            status="prepare",
            privacy="none",
            endorsements={},
            signed_date=None,
            issued_date=None,
            ca_download_url=None,
            last_updated_by=current_user._get_current_object(),
            updated_date=datetime.datetime.now(),
        )

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/purge_certificate")
@acl.roles_required("admin")
def purge_certificate(class_id):
    class_ = models.Class.objects.get(id=class_id)

    certificate_id = request.args.get("certificate_id", None)

    query = None
    if certificate_id:
        query = models.Certificate.objects(id=certificate_id, class_=class_)
    else:
        query = models.Certificate.objects(class_=class_)

    if query:
        query.update(
            status="purge",
            last_updated_by=current_user._get_current_object(),
            updated_date=datetime.datetime.now(),
        )

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/export_certificate")
@acl.roles_required("admin")
def export_certificate(class_id):
    class_ = models.Class.objects.get(id=class_id)
    required_signature = True
    txt_signature = request.args.get("signature", "on")
    if txt_signature == "off":
        required_signature = False

    certificates = pdf_utils.export_certificates(class_, required_signature)
    response = send_file(
        certificates,
        attachment_filename=f"{class_.id}-all.pdf",
        # as_attachment=True,
        mimetype="application/pdf",
    )

    return response


@module.route("/<class_id>/export_certificate_url")
@acl.roles_required("admin")
def export_certificate_url(class_id):
    class_ = models.Class.objects.get(id=class_id)

    certificates = models.Certificate.objects(class_=class_)
    row_list = []

    for certificate in certificates:
        participant = class_.get_participant(certificate.participant_id)
        if not participant:
            print(certificate.participant_id, participant)
            continue

        data = {
            "ID": certificate.participant_id,
            "Name": participant.name,
            "URL": certificate.get_validation_url(),
        }
        row_list.append(data)

    output = io.BytesIO()
    df = pandas.DataFrame(row_list)
    writer = pandas.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="Sheet1")
    writer.save()
    response = Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-disposition": f"attachment; filename=export-certificate-url.xlsx"
        },
    )

    return response
