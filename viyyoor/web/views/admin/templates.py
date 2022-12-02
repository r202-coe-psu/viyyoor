from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
    send_file,
    Response,
)
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.models import organizations
from viyyoor.web import acl, forms

module = Blueprint("templates", __name__, url_prefix="/templates")


@module.route("/", methods=["GET", "POST"])
@acl.roles_required("admin")
def index():
    classes = models.Class.objects(status="active").order_by("-id")
    templates = models.Template.objects(status="active").order_by("-id")
    form = forms.templates.CertificateTemplateForm()
    form.classes.choices = [(str(c.id), c.name) for c in classes]

    if not form.validate_on_submit():
        return render_template(
            "/admin/templates/index.html",
            form=form,
            templates=templates,
        )

    class_ = models.Class.objects.get(id=form.classes.data)
    certificate_template = models.CertificateTemplate()
    class_.certificate_templates[form.group.data] = certificate_template

    form.populate_obj(certificate_template)
    certificate_template.template = models.Template.objects.get(
        id=request.form.get("template_id")
    )
    certificate_template.last_updated_by = current_user._get_current_object()
    class_.save()

    return redirect(
        url_for("admin.classes.add_or_edit_certificate_template", class_id=class_.id)
    )


@module.route(
    "/create",
    methods=["GET", "POST"],
    defaults={"template_id": ""},
)
@module.route("/<template_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(template_id):
    form = forms.templates.TemplateForm()
    template = models.Template.objects()

    if template_id:
        template = models.Template.objects.get(id=template_id)
        form = forms.templates.TemplateForm(
            obj=template,
            uploaded_template_file=template.template_file,
            uploaded_thumbnail_file=template.thumbnail_file,
        )

    if not form.validate_on_submit():
        return render_template(
            "/admin/templates/create-edit.html",
            form=form,
            template=template,
        )

    if not template_id:
        template = models.Template(
            owner=current_user._get_current_object(),
            last_updated_by=current_user._get_current_object(),
        )

    form.populate_obj(template)

    if not template_id:
        if form.uploaded_template_file.data:
            template.template_file.put(
                form.uploaded_template_file.data,
                filename=form.uploaded_template_file.data.filename,
                content_type=form.uploaded_template_file.data.content_type,
            )
        if form.uploaded_thumbnail_file.data:
            template.thumbnail_file.put(
                form.uploaded_thumbnail_file.data,
                filename=form.uploaded_thumbnail_file.data.filename,
                content_type=form.uploaded_thumbnail_file.data.content_type,
            )
    else:
        if form.uploaded_template_file.data:
            template.template_file.replace(
                form.uploaded_template_file.data,
                filename=form.uploaded_template_file.data.filename,
                content_type=form.uploaded_template_file.data.content_type,
            )
        if form.uploaded_thumbnail_file.data:
            template.thumbnail_file.replace(
                form.uploaded_thumbnail_file.data,
                filename=form.uploaded_thumbnail_file.data.filename,
                content_type=form.uploaded_thumbnail_file.data.content_type,
            )

    template.share_status.last_updated_by = current_user._get_current_object()
    template.save()

    return redirect(url_for("admin.templates.index"))


@module.route("/<template_id>")
@acl.roles_required("admin")
def view(template_id):
    template = models.Template.objects.get(id=template_id)
    return render_template(
        "/admin/templates/view.html",
        template=template,
    )


@module.route("/<template_id>/delete")
@acl.roles_required("admin")
def delete(template_id):
    template = models.Template.objects.get(id=template_id)
    template.status = "delete"
    template.save()

    return redirect(url_for("admin.templates.index"))


@module.route("/<template_id>/template/<filename>")
@acl.roles_required("admin")
def download_template(template_id, filename):
    response = Response()
    response.status_code = 404

    template = models.Template.objects.get(id=template_id)

    if template:
        response = send_file(
            template.template_file,
            download_name=template.template_file.filename,
            mimetype=template.template_file.content_type,
        )

    return response


@module.route("/<template_id>/thumbnail/<filename>")
@acl.roles_required("admin")
def download_thumbnail(template_id, filename):
    response = Response()
    response.status_code = 404

    template = models.Template.objects.get(id=template_id)

    if template:
        response = send_file(
            template.thumbnail_file,
            download_name=template.thumbnail_file.filename,
            mimetype=template.thumbnail_file.content_type,
        )

    return response


@module.route("/<template_id>/set_sharing_status", methods=["GET", "POST"])
@acl.roles_required("admin")
def set_share_status(template_id):
    template = models.Template.objects.get(id=template_id)
    form = forms.templates.ShareStatusTemplateForm(obj=template)
    form.organizations.choices = [
        (str(o.id), o.name) for o in models.Organization.objects().order_by("-id")
    ]

    if not form.validate_on_submit():
        form.status.data = template.share_status.status
        if template.share_status.status == "shared":
            form.organizations.data = [
                str(o.id) for o in template.share_status.organizations
            ]
        return render_template(
            "/admin/templates/set-share-status.html",
            form=form,
        )

    if form.status.data == "shared":
        template.share_status.organizations = [
            models.Organization.objects.get(id=oid) for oid in form.organizations.data
        ]
        if len(template.share_status.organizations) == 0:
            form.status.data = "unshared"
            form.organizations = None
    template.share_status.status = form.status.data
    template.share_status.updated_date = datetime.datetime.now
    template.share_status.last_updated_by = current_user._get_current_object()
    template.save()

    return redirect(url_for("admin.templates.index"))
