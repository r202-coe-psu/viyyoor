from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    request,
    Response,
    current_app,
    abort,
)
from flask_login import current_user

import datetime
import pathlib

import pandas
import xlsxwriter
import json
import io
from copy import deepcopy
from urllib import parse

from viyyoor import models
from viyyoor.web import acl, forms, redis_rq

from viyyoor.utils import pdf_utils
from viyyoor.utils import certificate_utils
from viyyoor.utils import digital_signature_utils

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
            class_=class_,
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
    job_keys = {
        f"prepare certificates": f"prepare_certificates_{class_.id}",
        f"export certificates": f"export_certificates_{class_.id}_on",
        f"export certificates without signature": f"export_certificates_{class_.id}_off",
    }

    jobs = {}
    job_data = {}
    for key, job_id in job_keys.items():
        jobs[key] = redis_rq.redis_queue.get_job(job_id)
        if "export" in key:
            job_data[key] = pathlib.Path(
                f"{current_app.config['VIYYOOR_CACHE_DIR']}/{job_id}.pdf"
            )

    return render_template(
        "/admin/classes/view.html",
        class_=class_,
        jobs=jobs,
        job_data=job_data,
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
    form.user.queryset = users

    if not form.validate_on_submit():
        endorser_ids = class_.endorsers.keys()
        form.endorser_id.choices = [
            idx
            for idx in form.endorser_id.choices
            if idx[0] not in endorser_ids or idx[0] == form.endorser_id.data
        ]

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


def set_certificate_logo_form(form, class_, index):
    form.logo.choices = [(str(logo.id), "") for logo in models.Logo.objects()]
    form.logo.choices.insert(0, (None, "-"))

    return form


def get_url_download_logo_images(format=""):
    logos = models.Logo.objects()
    data = []

    for logo in logos:
        data.append(
            dict(
                id=str(logo.id),
                uri=url_for(
                    "admin.organizations.download_logo",
                    logo_id=logo.id,
                    thumbnail="thumbnail",
                    filename=logo.logo_file.filename,
                ),
            )
        )

    if format == "json":
        return json.dumps(data)

    return data


@module.route("/<class_id>/select_certificate_logos")
@acl.roles_required("admin")
def select_certificate_logos(class_id):
    class_ = models.Class.objects.get(id=class_id)
    logos = models.Logo.objects(status="active")
    form = forms.classes.GroupCertificateLogoForm()

    LOGO_AMOUNT = 5
    for n in range(LOGO_AMOUNT):
        try:
            order = class_.certificate_logos[n].order
            logo = class_.certificate_logos[n].logo.id
        except:
            order = 0
            logo = ""

        form.certificate_logos.append_entry(
            {
                "order": order,
                "logo": logo,
            }
        )

    return render_template(
        "/admin/classes/select-certificate-logos.html",
        class_=class_,
        logos=logos,
        LOGO_AMOUNT=LOGO_AMOUNT,
        form=form,
        url_download_logo_images=get_url_download_logo_images(format="json"),
        set_certificate_logo_form=set_certificate_logo_form,
    )


@module.route("/<class_id>/submit_certificate_logos_selection", methods=["GET", "POST"])
@acl.roles_required("admin")
def submit_certificate_logo_selection(class_id):
    class_ = models.Class.objects.get(id=class_id)
    form = forms.classes.GroupCertificateLogoForm()
    for f in form.certificate_logos:
        f.logo.choices = [
            (str(logo.id), logo.logo_name) for logo in models.Logo.objects()
        ]

    if not form.validate_on_submit():
        return redirect(
            url_for(
                "admin.classes.select_certificate_logos",
                class_id=class_.id,
                organization_id=request.args.get("organization_id"),
            )
        )

    class_.certificate_logos = [
        models.CertificateLogo(
            logo=models.Logo.objects.get(id=cert_form["logo"]),
            order=cert_form["order"],
            last_updated_by=current_user._get_current_object(),
        )
        for cert_form in form.certificate_logos.data
        if cert_form["logo"] != "None"
    ]

    class_.certificate_logos = sorted(class_.certificate_logos, key=lambda x: x.order)

    class_.save()
    return redirect(
        url_for(
            "admin.classes.view",
            class_id=class_.id,
            organization_id=request.args.get("organization_id"),
        )
    )


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
        class_.participants[str(participant.id)] = participant
    # else:
    #     class_.participants.pop(str(participant.id))

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
    "/<class_id>/participants/check-duplicate-from-file",
    methods=["GET", "POST"],
)
@acl.roles_required("admin")
def check_duplicate_participant_from_file(class_id):
    class_ = models.Class.objects.get(id=class_id)
    form = forms.classes.ParticipantFileForm()

    data = []
    dfs = pandas.read_excel(form.participant_file.data)
    dfs.columns = dfs.columns.str.lower()
    for index, row in dfs.iterrows():
        for p_id in class_.participants:
            p = class_.get_participant(p_id)

            common_id = str(row["common_id"]).strip()
            participant_common_id = common_id

            if "name" in dfs.columns:
                participant_name = str(row["name"]).strip()

            if "first_name" in dfs.columns and "last_name" in dfs.columns:
                participant_name = f"{row['first_name']} {row['last_name']}"

            if "title" in dfs.columns:
                participant_name = f"{row['title']}{participant_name}"

            if participant_common_id == p.common_id or participant_name == p.name:
                participant_dict = dict(
                    name=p.name, common_id=p.common_id, group=p.group.title()
                )
                if participant_dict in data:
                    continue

                data.append(participant_dict)

    return data


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
        participant = None
        if "id" in dfs.columns:
            participant = class_.get_participant(row["id"])
        else:
            participant = models.Participant()

        common_id = str(row["common_id"]).strip()
        participant.common_id = common_id

        participant.group = "participant"
        if "grade" in dfs.columns:
            if row["grade"] in [
                "A",
                "B+",
                "B",
                "C+",
                "C",
                "D+",
                "D",
                "E",
                "W",
            ]:
                if row["grade"] in ["A", "B+", "B", "C+", "C"]:
                    participant.group = "achievement"
                elif row["grade"] in ["D+", "D"]:
                    participant.group = "participant"
                else:
                    continue

        if "group" in dfs.columns:
            participant.group = row["group"]
        else:
            participant.group = "participant"

        class_.participants[str(participant.id)] = participant
        participant_name = ""

        if "name" in dfs.columns:
            participant_name = str(row["name"]).strip()

        if "first_name" in dfs.columns and "last_name" in dfs.columns:
            participant_name = f"{row['first_name']} {row['last_name']}"

        if "title" in dfs.columns:
            participant_name = f"{row['title']}{participant_name}"

        if "email" in dfs.columns:
            participant.email = row["email"]

        if "organization" in dfs.columns:
            participant.organization = row["organization"]

        if "academy" in dfs.columns:
            participant.organization = row["academy"]

        participant.name = participant_name
        participant.last_updated_by = current_user._get_current_object()
        participant.updated_date = datetime.datetime.now()
        participant.extra = row.to_dict()

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

    kwargs = {
        "validated_url_template": request.host_url[:-1]
        + parse.unquote(url_for("certificates.view", certificate_id="{certificate_id}"))
    }

    job = redis_rq.redis_queue.queue.enqueue(
        certificate_utils.create_certificates,
        args=(class_, current_user._get_current_object()),
        kwargs=kwargs,
        job_id=f"prepare_certificates_{class_.id}",
        timeout=600,
        job_timeout=600,
    )
    print("submit", job.get_id())
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
    if txt_signature not in ["on", "off"]:
        txt_signature = "on"

    if txt_signature == "off":
        required_signature = False

    # certificates = pdf_utils.export_certificates(class_, required_signature)
    # response = send_file(
    #     certificates,
    #     attachment_filename=f"{class_.id}-all.pdf",
    #     # as_attachment=True,
    #     mimetype="application/pdf",
    # )

    # return response
    VIYYOOR_CACHE_DIR = current_app.config.get("VIYYOOR_CACHE_DIR")
    filename = (
        f"{VIYYOOR_CACHE_DIR}/export_certificates_{class_.id}_{txt_signature}.pdf"
    )
    p = pathlib.Path(filename)
    if p.exists():
        p.unlink(missing_ok=True)

    kwargs = {
        "filename": filename,
        "validated_url_template": request.host_url[:-1]
        + url_for("certificates.view", certificate_id="{certificate_id}"),
    }
    job = redis_rq.redis_queue.queue.enqueue(
        pdf_utils.export_certificates,
        args=(class_, required_signature),
        kwargs=kwargs,
        job_id=f"export_certificates_{class_.id}_{txt_signature}",
        timeout=600,
        job_timeout=600,
    )
    print("submit", job.get_id())
    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/export_certificate_url")
@acl.roles_required("admin")
def export_certificate_url(class_id):
    class_ = models.Class.objects.get(id=class_id)

    certificates = models.Certificate.objects(class_=class_)
    row_list = []
    including_keys = ["academy", "project_name"]

    for certificate in certificates:
        participant = class_.get_participant(certificate.participant_id)
        if not participant:
            continue

        data = {
            "ID": certificate.id,
            "Name": participant.name,
            "URL": certificate.validated_url,
        }

        for key in including_keys:
            if key in participant.extra:
                data[key] = participant.extra[key]

        row_list.append(data)

    output = io.BytesIO()
    df = pandas.DataFrame(row_list)
    writer = pandas.ExcelWriter(output, engine="xlsxwriter")
    df.index += 1
    df.to_excel(
        writer,
        sheet_name="URL",
    )
    writer.save()
    response = Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-disposition": f"attachment; filename=export-certificate-url.xlsx"
        },
    )

    return response


@module.route("/<class_id>/export_participant_data")
@acl.roles_required("admin")
def export_participant_data(class_id):
    class_ = models.Class.objects.get(id=class_id)
    row_list = []

    for pid, participant in class_.participants.items():
        data = {
            "ID": pid,
            "common_id": participant.common_id,
            "name": participant.name,
            "group": participant.group,
        }
        data.update(participant.extra)
        row_list.append(data)

    output = io.BytesIO()
    df = pandas.DataFrame(row_list)
    writer = pandas.ExcelWriter(output, engine="xlsxwriter")
    df.index += 1
    df.to_excel(
        writer,
        sheet_name="Sheet1",
    )
    writer.save()
    response = Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-disposition": f"attachment; filename=export-participant_data.xlsx"
        },
    )

    return response


@module.route("/<class_id>/download/<filename>")
@acl.roles_required("admin")
def download(class_id, filename):
    p = pathlib.Path(f"{current_app.config['VIYYOOR_CACHE_DIR']}/{filename}")
    if not p.exists():
        return abort(404)

    class_ = models.Class.objects.get(id=class_id)
    if not class_:
        return abort(404)

    f = open(p, "rb")
    response = send_file(
        f,
        download_name=filename,
        # as_attachment=True,
        mimetype="application/pdf",
    )

    return response


@module.route("/<class_id>/endorse/force", methods=["GET", "POST"])
@acl.roles_required("admin")
def force_endorse(class_id):
    class_ = models.Class.objects.get(id=class_id)

    certificates = models.Certificate.objects(class_=class_, status="prerelease")

    for certificate in certificates:
        # sign signature hear1
        # sign_digital_signature(user, certificate, password)

        for endorser_id, endorser in class_.endorsers.items():
            endorsement = models.Endorsement(
                endorser=endorser.user,
                ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
                remark=f"force endorsement by {current_user.username} ({current_user.id})",
            )

            if endorser.endorser_id not in certificate.endorsements:
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
            certificate.status = "signing"

        certificate.updated_date = datetime.datetime.now()
        certificate.save()

    job = redis_rq.redis_queue.queue.enqueue(
        digital_signature_utils.sign_certificates,
        args=(class_id, current_app.config),
        job_id=f"endorsements_certificates_{class_.id}",
        timeout=600,
        job_timeout=600,
    )

    return redirect(url_for("admin.classes.view", class_id=class_id))
