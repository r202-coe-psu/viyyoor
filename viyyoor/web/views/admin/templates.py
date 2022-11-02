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
    if template_id:
        template = models.Template.objects.get(id=template_id)
        form = forms.templates.TemplateForm(obj=template)

    if not form.validate_on_submit():
        return render_template(
            "/admin/templates/create-edit.html",
            form=form,
        )

    if not template_id:
        template = models.Template(
            owner=current_user._get_current_object(),
            last_updated_by=current_user._get_current_object(),
        )

    form.populate_obj(template)

    if not template_id:
        template.file.put(
            form.template_file.data,
            filename=form.template_file.data.filename,
            content_type=form.template_file.data.content_type,
        )
        template.thumbnail.put(
            form.thumbnail_file.data,
            filename=form.thumbnail_file.data.filename,
            content_type=form.thumbnail_file.data.content_type,
        )
    else:
        template.file.replace(
            form.template_file.data,
            filename=form.template_file.data.filename,
            content_type=form.template_file.data.content_type,
        )
        template.thumbnail.replace(
            form.thumbnail_file.data,
            filename=form.thumbnail_file.data.filename,
            content_type=form.thumbnail_file.data.content_type,
        )

    template.control.updated_by = current_user._get_current_object()
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


@module.route("/<template_id>/<filename>")
@acl.roles_required("admin")
def download(template_id, filename):
    response = Response()
    response.status_code = 404

    template = models.Template.objects.get(id=template_id)

    if template:
        response = send_file(
            template.file,
            download_name=template.file.filename,
            # as_attachment=True,
            mimetype=template.file.content_type,
        )

    return response


@module.route("/<template_id>/<thumbnail>")
@acl.roles_required("admin")
def thumbnail_show(template_id, thumbnail):
    response = Response()
    response.status_code = 404

    template = models.Template.objects.get(id=template_id)

    if template:
        response = send_file(
            template.file,
            thumbnail_name=template.file.thumbnail,
            # as_attachment=True,
            mimetype=template.file.content_type,
        )

    return response


@module.route("/<template_id>/set_control", methods=["GET", "POST"])
@acl.roles_required("admin")
def set_control(template_id):
    template = models.Template.objects.get(id=template_id)
    form = forms.templates.ControlTemplateForm(obj=template)
    form.organizations.choices = [
        (str(o.id), o.name) for o in models.Organization.objects().order_by("-id")
    ]

    if not form.validate_on_submit():
        form.status.data = template.control.status
        if template.control.status == "shared":
            form.organizations.data = [
                str(o.id) for o in template.control.organizations
            ]
        return render_template(
            "/admin/templates/set-control.html",
            form=form,
        )

    if form.status.data == "shared":
        template.control.organizations = [
            models.Organization.objects.get(id=oid) for oid in form.organizations.data
        ]
        if len(template.control.organizations) == 0:
            form.status.data = "unshared"
            form.organizations = None
    template.control.status = form.status.data
    template.control.updated_date = datetime.datetime.now
    template.control.last_updated_by = current_user._get_current_object()
    template.save()

    return redirect(url_for("admin.templates.index"))
