from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    send_file,
    Response,
)
from flask_login import current_user, login_required

import datetime

from viyyoor.web import acl, forms
from viyyoor import models


module = Blueprint("organizations", __name__, url_prefix="/organizations")


@module.route("/")
def index():
    return redirect(url_for("dashboard.index"))


@module.route(
    "/logos/<logo_id>/download/<filename>",
    defaults=dict(thumbnail=""),
)
@module.route("/logos/<logo_id>/download/<thumbnail>/<filename>")
def download_logo(logo_id, filename, thumbnail):
    response = Response()
    response.status_code = 404
    logo = models.Logo.objects.get(id=logo_id)

    image = logo.logo_file
    content_type = logo.logo_file.content_type
    if thumbnail == "thumbnail":
        image = logo.logo_file.thumbnail
        content_type = logo.logo_file.thumbnail.content_type

    if logo:
        response = send_file(
            image,
            download_name=filename,
            mimetype=content_type,
        )

    return response


@module.route("/logos", methods=["GET", "POST"])
@acl.roles_required("admin")
def logos():
    logos = models.Logo.objects()
    return render_template(
        "/admin/organizations/logos.html",
        logos=logos,
    )


@module.route("/logos/add", methods=["GET", "POST"], defaults={"logo_id": ""})
@module.route(
    "/logos/<logo_id>/edit",
    methods=["GET", "POST"],
)
@acl.roles_required("admin")
def add_or_edit_logo(logo_id):
    logo = models.Logo()
    form = forms.organizations.LogoForm()

    if logo_id:
        logo = models.Logo.objects.get(id=logo_id)
        form = forms.organizations.LogoForm(obj=logo)

    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/add-edit-logo.html",
            form=form,
        )

    form.populate_obj(logo)

    if not logo_id:
        if form.uploaded_logo_file.data:
            logo.logo_file.put(
                form.uploaded_logo_file.data,
                filename=form.uploaded_logo_file.data.filename,
                content_type=form.uploaded_logo_file.data.content_type,
            )
    else:
        if form.uploaded_logo_file.data:
            logo.logo_file.replace(
                form.uploaded_logo_file.data,
                filename=form.uploaded_logo_file.data.filename,
                content_type=form.uploaded_logo_file.data.content_type,
            )

    logo.uploaded_by = current_user._get_current_object()
    logo.uploaded_date = datetime.datetime.now()
    logo.save()

    return redirect(url_for("admin.organizations.logos"))


@module.route("/logos/<logo_id>/delete")
@acl.roles_required("admin")
def delete_logo(logo_id):
    organization = models.Organization.objects.get(id=organization_id)
    logo = models.Logo.objects.get(id=logo_id)
    logo.delete()

    return redirect(
        url_for("admin.organizations.view_logos", organization_id=organization_id)
    )


@module.route("/certificates", methods=["GET", "POST"])
@acl.roles_required("admin")
def view_certificates():
    organization = models.Organization.objects.get(id=organization_id)
    classes = models.Class.objects(organization=organization)
    certificates = models.Certificate.objects(class___in=classes)

    search_form = forms.certificates.CertificateSearchForm()
    search_form.class_.choices = [("-", "-")] + [(c.id, c.name) for c in classes]

    if not search_form.validate_on_submit():
        return render_template(
            "/admin/organizations/certificates.html",
            certificates=certificates,
            organization=organization,
            search_form=search_form,
            get_class_name=get_class_name,
        )

    if search_form.class_.data != "-":
        certificates = certificates.filter(class_=search_form.class_.data)

    certificates = [
        c
        for c in certificates
        if search_form.owner.data.lower() in c.get_participant_name().lower()
    ]

    search_form.class_.choices = [("-", "-")] + [(c.id, c.name) for c in classes]
    return render_template(
        "/admin/organizations/certificates.html",
        certificates=certificates,
        organization=organization,
        search_form=search_form,
        get_class_name=get_class_name,
    )
