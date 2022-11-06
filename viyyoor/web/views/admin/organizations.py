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
from ....models.organizations import Endorser, Administrator


module = Blueprint("organizations", __name__, url_prefix="/organizations")


@module.route("/")
def index():
    if current_user.has_roles(["superadmin"]):
        organizations = models.Organization.objects(
            status="active",
        )
    else:
        organizations = []
        all_organizations = models.Organization.objects(
            status="active",
        )
        for o in all_organizations:
            for a in o.admins:
                if a.user == current_user:
                    organizations.append(o)

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
        organization = models.organizations.Organization.objects.get(id=organization_id)
        form = forms.organizations.OrganizationForm(obj=organization)

    form.admins.choices = [(str(u.id), u.get_fullname()) for u in models.User.objects()]
    if not form.validate_on_submit():
        if organization:
            form.admins.data = [str(a.user.id) for a in organization.admins]

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

    organization.admins = [
        Administrator(
            user=models.User.objects.get(id=u_id),
            created_by=current_user._get_current_object(),
        )
        for u_id in form.admins.data
    ]
    organization.save()

    for u_id in form.admins.data:
        user = models.User.objects.get(id=u_id)
        if organization not in user.organizations:
            user.organizations.append(organization)
            user.save()

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


@module.route("/<organization_id>/admins", methods=["GET", "POST"])
@acl.roles_required("admin")
def view_admins(organization_id):
    organization = models.organizations.Organization.objects.get(id=organization_id)

    form = forms.organizations.OrganizationAdminsForm()
    form.admins.choices = [
        (str(u.id), u.get_fullname())
        for u in models.User.objects(organizations__in=[organization])
        if u not in [a.user for a in organization.admins]
    ]
    if not form.validate_on_submit():
        return render_template(
            "/admin/organizations/view-admins.html",
            organization=organization,
            form=form,
        )

    for u_id in form.admins.data:
        organization.admins.append(
            Administrator(
                user=models.User.objects.get(id=u_id),
                created_by=current_user._get_current_object(),
            )
        )

    organization.save()

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
    organization = models.organizations.Organization.objects.get(id=organization_id)

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
            Endorser(
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
