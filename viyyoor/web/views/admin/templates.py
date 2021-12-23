from flask import (
        Blueprint, 
        render_template, 
        redirect, 
        url_for, 
        send_file,
        Response,
        )
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("templates", __name__, url_prefix="/templates")


@module.route("/")
@acl.roles_required("admin")
def index():
    templates = models.Template.objects(status="active")
    return render_template(
        "/admin/templates/index.html",
        templates=templates,
    )


@module.route(
    "/create",
    methods=["GET", "POST"],
    defaults={"template_id": None},
)
@module.route("/<template_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(template_id):
    form = forms.templates.TemplateForm()
    if template_id:
        template = models.Class.objects.get(id=template_id)
        form = forms.templates.ClassForm(obj=template)

    if not form.validate_on_submit():
        return render_template(
            "/admin/templates/create-edit.html",
            form=form,
        )

    if not template_id:
        template = models.Template(
            owner = current_user._get_current_object(),
            last_updated_by = current_user._get_current_object(),
            )

    form.populate_obj(template)

    if not template_id:
        template.file.put(
                form.template_file.data,
                filename=form.template_file.data.filename,
                content_type=form.template_file.data.content_type,
                )
    else: 

        template.file.replace(
                form.template_file.data,
                filename=form.template_file.data.filename,
                content_type=form.template_file.data.content_type,
                )

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


@module.route('/<template_id>/<filename>')
@acl.roles_required("admin")
def download(template_id, filename):
    response = Response()
    response.status_code = 404


    template = models.Template.objects.get(id=template_id)

        
    if template:
        response = send_file(
            template.file,
            attachment_filename=template.file.filename,
            # as_attachment=True,
            mimetype=template.file.content_type)

    return response

