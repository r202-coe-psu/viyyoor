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
    classes = models.Class.objects(organization=organization)
    return render_template(
        "/admin/organizations/view.html",
        organization=organization,
        classes=classes,
    )


@module.route("/<organization_id>/admins", methods=["GET", "POST"])
@acl.roles_required("admin")
def view_admins(organization_id):
    organization = models.organizations.Organization.objects.get(id=organization_id)

    form = forms.organizations.OrganizationAdminsForm()
    form.admins.choices = [
        (str(u.id), u.get_fullname())
        for u in models.OrganizationUserRole.objects(organization=organization)
        if u.role != "admin"
    ]
    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/view-admins.html",
            organization=organization,
            form=form,
        )

    for u_id in form.admins.data:
        user = models.User.objects.get(id=u_id)
        org_user = models.OrganizationUserRole.objects(
            organization=organization,
            user=user,
            role="admin",
            added_by=current_user._get_current_object(),
            last_modifier=current_user._get_current_object(),
        )
        org_user.save()

    return redirect(
        url_for(
            "admin.organizations.view_admins",
            organization_id=organization.id,
            form=form,
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


@module.route("/<organization_id>/endorsers", methods=["GET", "POST"])
@acl.roles_required("admin")
def view_endorsers(organization_id):
    organization = models.Organization.objects.get(id=organization_id)

    form = forms.organizations.OrganizationEndorsersForm()
    form.endorsers.choices = [
        (str(u.id), u.get_fullname())
        for u in models.User.objects(organizations__in=[organization])
        if u not in [e.user for e in organization.endorsers]
    ]
    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/view-endorsers.html",
            organization=organization,
            form=form,
        )

    for u_id in form.endorsers.data:
        organization.endorsers.append(
            models.organizations.Endorser(
                user=models.User.objects.get(id=u_id),
                created_by=current_user._get_current_object(),
            )
        )

    organization.save()

    return redirect(
        url_for(
            "admin.organizations.view_endorsers",
            organization_id=organization.id,
            form=form,
        )
    )


@module.route("/<organization_id>/endorsers/<user_id>/delete")
@acl.roles_required("admin")
def delete_endorser(organization_id, user_id):
    organization = models.Organization.objects.get(id=organization_id)
    user = models.User.objects.get(id=user_id)
    for a in organization.endorsers:
        if a.user == user:
            organization.endorsers.remove(a)
    organization.save()

    return redirect(
        url_for("admin.organizations.view_endorsers", organization_id=organization.id)
    )


@module.route("/<organization_id>/logos", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_logo(organization_id):

    form = forms.organizations.OrganizationForm()
    if organization_id:
        organization = models.Organization.objects.get(id=organization_id)
        form = forms.organizations.OrganizationForm(obj=organization)

    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/add-logo.html",
            organization=organization,
            form=form,
        )

    form.populate(organization)

    if not organization_id:
        if form.uploaded_logos.data:
            organization.logos.put(
                form.uploaded_logos.data,
                filename=form.uploaded_logosdata.filename,
                content_type=form.uploaded_logos.data.content_type,
            )
    else:
        if form.uploaded_logos.data:
            organization.logos.replace(
                form.uploaded_logos.data,
                filename=form.uploaded_logos.data.filename,
                content_type=form.uploaded_logos.data.content_type,
            )

    organization.save()

    return redirect(
        url_for("admin.organizations.index", organization_id=organization_id)
    )
