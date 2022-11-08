from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
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
@acl.roles_required("superadmin")
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
@acl.roles_required("superadmin")
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
    classes = models.Class.objects(organization=organization)
    return render_template(
        "/admin/organizations/view.html",
        organization=organization,
        classes=classes,
    )


@module.route("/<organization_id>/<role>s/", methods=["GET", "POST"])
@acl.roles_required("admin")
def view_users_by_role(organization_id, role):
    organization = models.organizations.Organization.objects.get(id=organization_id)

    form = forms.organizations.OrganizationUserRoleForm()
    form.users.choices = [
        (str(org_user.id), org_user.user.get_fullname())
        for org_user in models.OrganizationUserRole.objects(organization=organization)
        if org_user.role != role
    ]
    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/view-users-by-role.html",
            organization=organization,
            form=form,
            role=role,
        )

    for u_id in form.users.data:
        org_user = models.OrganizationUserRole.objects.get(id=u_id)
        org_user.role = role
        org_user.save()

    return redirect(
        url_for(
            "admin.organizations.view_users_by_role",
            organization_id=organization.id,
            role=role,
        )
    )


@module.route("/<organization_id>/admin/<user_id>/delete")
@acl.roles_required("admin")
def delete_admin(organization_id, user_id):
    organization = models.Organization.objects.get(id=organization_id)
    user = models.User.objects.get(id=user_id)
    for a in organization.admins:
        if a.user == user:
            organization.admins.remove(a)
    organization.save()

    return redirect(
        url_for("admin.organizations.view_admins", organization_id=organization.id)
    )


@module.route("/<organization_id>/logos", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_logo(organization_id):
    organization = models.Organization.objects.get(id=organization_id)
    logo = models.Certificate_logo()
    form = forms.organizations.OrganizationLogoForm()

    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/add-logo.html",
            organization=organization,
            form=form,
        )

    form.populate_obj(logo)

    logo.logo_file.put(
        form.uploaded_logo_file.data,
        filename=form.uploaded_logo_file.data.filename,
        content_type=form.uploaded_logo_file.data.content_type,
    )

    print(form.logo_name.data)
    logo.save()

    return redirect(url_for("admin.organizations.index"))


@module.route("/<organization_id>/logos/<filename>")
@acl.roles_required("admin")
def download_logo(organization_id, filename):
    response = response()
    response.status_code = 404

    organization = models.Organization.objects.get(id=organization_id)

    if organization:
        response = send_file(
            organization.uploaded_logos,
            download_name=organization.uploaded_logos.filename,
            mimetype=organization.uploaded_logos.content_type,
        )

    return response
