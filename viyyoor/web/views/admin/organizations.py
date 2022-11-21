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

    # organizations = []
    organizations = models.Organization.objects(
        status="active",
    )

    # for o in all_organizations:
    #     for a in o.admins:
    #         if a.user == current_user:
    #             organizations.append(o)

    return render_template(
        "/admin/organizations/index.html",
        now=datetime.datetime.now,
        organizations=organizations,
    )


@module.route(
    "/create",
    methods=["GET", "POST"],
    defaults={"organization_id": None},
)
@module.route("/<organization_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(organization_id):
    form = forms.organizations.OrganizationForm()
    organization = None

    if organization_id:
        organization = models.Organization.objects.get(id=organization_id)
        form = forms.organizations.OrganizationForm(obj=organization)

    if not form.validate_on_submit():

        return render_template(
            "/admin/organizations/create-edit.html",
            form=form,
        )

    if not organization_id:
        organization = models.Organization()
        organization.created_by = current_user._get_current_object()

    form.populate_obj(organization)

    organization.last_updated_by = current_user._get_current_object()
    organization.last_updated_date = datetime.datetime.now()

    organization.save()

    return redirect(url_for("admin.organizations.index"))


@module.route("/<organization_id>/delete")
@acl.roles_required("admin")
def delete(organization_id):
    organization = models.Organization.objects.get(
        id=organization_id,
    )
    organization.status = "inactive"
    organization.save()

    return redirect(url_for("admin.organizations.index"))


@module.route("/<organization_id>")
@acl.roles_required("admin")
def view(organization_id):
    organization = models.Organization.objects.get(
        id=organization_id,
        status="active",
    )
    logos = models.CertificateLogo.objects()
    classes = models.Class.objects(organization=organization)
    return render_template(
        "/admin/organizations/view.html",
        logos=logos,
        organization=organization,
        classes=classes,
    )


@module.route("/<organization_id>/users", methods=["GET", "POST"])
@acl.roles_required("admin")
def view_users(organization_id):
    organization = models.organizations.Organization.objects.get(id=organization_id)
    role = request.args.get("role")
    organization_user_roles = organization.get_users()
    if role not in ["all", None]:
        organization_user_roles = organization_user_roles.filter(role=role)

    org_user_forms = {}
    for u in organization_user_roles:
        org_user_forms[u.id] = forms.organizations.OrganizationRoleSelectionForm(obj=u)

    if request.args.get("user_role_id"):
        user_role = models.OrganizationUserRole.objects.get(
            id=request.args.get("user_role_id")
        )
        form = org_user_forms[user_role.id]
        if form.validate_on_submit():
            user_role.role = form.role.data
            user_role.save()
            return redirect(
                url_for(
                    "admin.organizations.view_users",
                    organization_id=organization.id,
                    role=role,
                )
            )

    return render_template(
        "/admin/organizations/users.html",
        organization=organization,
        organization_user_roles=organization_user_roles,
        role=role,
        org_user_forms=org_user_forms,
    )


@module.route("/<organization_id>/logos", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_logo(organization_id):
    organization = models.Organization.objects.get(id=organization_id)
    logo = models.CertificateLogo()
    form = forms.organizations.OrganizationLogoForm()

    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/add-logo.html",
            organization=organization,
            form=form,
        )

    form.populate_obj(logo)

    if logo.logo_file:
        logo.logo_file.put(
            form.uploaded_logo_file.data,
            filename=form.uploaded_logo_file.data.filename,
            content_type=form.uploaded_logo_file.data.content_type,
        )

    else:
        logo.logo_file.replace(
            form.uploaded_logo_file.data,
            filename=form.uploaded_logo_file.data.filename,
            content_type=form.uploaded_logo_file.data.content_type,
        )

    logo.uploaded_by = current_user._get_current_object()

    logo.save()

    return redirect(
        url_for("admin.organizations.view", organization_id=organization_id)
    )


@module.route("/<organization_id>/logos/<filename>")
@acl.roles_required("admin")
def show_logo(organization_id, filename):
    response = Response()
    response.status_code = 404

    organization = models.Organization.objects.get(id=organization_id)
    logo = models.CertificateLogo.objects.get(id=filename)

    if logo:
        response = send_file(
            logo.logo_file,
            download_name=logo.logo_file.filename,
            mimetype=logo.logo_file.content_type,
        )

    return response


@module.route("/<organization_id>/<logo_id>/delete")
@acl.roles_required("admin")
def delete_logo(organization_id, logo_id):
    organization = models.Organization.objects.get(id=organization_id)
    logo = models.CertificateLogo.objects.get(id=logo_id)
    logo.delete()

    return redirect(
        url_for("admin.organizations.view", organization_id=organization_id)
    )
