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
            organization=organization,
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
    logos = models.CertificateLogo.objects(organization=organization)
    classes = models.Class.objects(organization=organization, status="active")
    return render_template(
        "/organizations/view.html",
        logos=logos,
        organization=organization,
        classes=classes,
    )


@module.route("/<organization_id>/classes", methods=["GET", "POST"])
@acl.organization_roles_required("admin", "endorser", "staff")
def view_classes(organization_id):
    organization = models.Organization.objects.get(
        id=organization_id,
        status="active",
    )
    classes = models.Class.objects(organization=organization, status="active")
    return render_template(
        "/organizations/classes.html",
        organization=organization,
        classes=classes,
    )


@module.route("/<organization_id>/logos", methods=["GET", "POST"])
@acl.organization_roles_required("admin", "endorser", "staff")
def view_logos(organization_id):
    organization = models.Organization.objects.get(id=organization_id)
    logos = models.CertificateLogo.objects(organization=organization)
    return render_template(
        "/organizations/logos.html",
        organization=organization,
        logos=logos,
    )


@module.route("/<organization_id>/users", methods=["GET", "POST"])
@acl.organization_roles_required("admin", "endorser", "staff")
def view_users(organization_id):
    organization = models.organizations.Organization.objects.get(id=organization_id)
    role = request.args.get("role")
    organization_user_roles = organization.get_users()
    if role not in ["all", None]:
        organization_user_roles = organization_user_roles.filter(role=role)
    if request.args.get("status") == "disactive":
        organization_user_roles = models.OrganizationUserRole.objects(
            status="disactive", organization=organization
        )

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
                    "organizations.view_users",
                    organization_id=organization.id,
                    role=role,
                )
            )

    add_member_form = forms.organizations.OrgnaizationAddMemberForm()
    add_member_form.members.choices = [
        (str(u.id), u.get_fullname())
        for u in models.User.objects(organizations__nin=[organization])
    ]

    return render_template(
        "/organizations/users.html",
        organization=organization,
        organization_user_roles=organization_user_roles,
        role=role,
        org_user_forms=org_user_forms,
        add_member_form=add_member_form,
    )


@module.route("/<organization_id>/templates", methods=["GET", "POST"])
@acl.organization_roles_required("admin", "endorser", "staff")
def view_templates(organization_id):
    organization = models.Organization.objects.get(id=organization_id)

    classes = models.Class.objects(status="active", organization=organization).order_by(
        "-id"
    )
    templates = models.Template.objects(
        status="active", organization=organization
    ).order_by("-id")
    form = forms.templates.CertificateTemplateForm()
    form.classes.choices = [(str(c.id), c.name) for c in classes]

    if not form.validate_on_submit():
        return render_template(
            "/organizations/templates.html",
            form=form,
            templates=templates,
            organization=organization,
        )

    class_ = models.Class.objects.get(id=form.classes.data)
    certificate_template = models.CertificateTemplate(organization=organization)
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


@module.route("/<organization_id>/users/submit_add_members", methods=["POST"])
@acl.organization_roles_required("admin")
def submit_add_members(organization_id):
    organization = models.Organization.objects.get(id=organization_id)
    form = forms.organizations.OrgnaizationAddMemberForm()
    form.members.choices = [
        (str(u.id), u.get_fullname())
        for u in models.User.objects(organizations__nin=[organization])
    ]

    if not form.validate_on_submit():
        return redirect(
            url_for("organizations.view_users", organization_id=organization.id)
        )

    for u in form.members.data:
        user = models.User.objects.get(id=u)
        user.organizations.append(organization)
        if not user.get_current_organization():
            user.user_setting.current_organization = organization
        user.save()

        org_user = models.OrganizationUserRole(
            organization=organization,
            user=user,
            added_by=current_user._get_current_object(),
            last_modifier=current_user._get_current_object(),
        )
        org_user.save()

    return redirect(
        url_for("organizations.view_users", organization_id=organization.id)
    )


@module.route(
    "/<organization_id>/users/<organization_user_id>/<operator>",
    methods=["GET", "POST"],
)
@acl.organization_roles_required("admin")
def manage_user(organization_id, organization_user_id, operator):
    organization = models.Organization.objects.get(id=organization_id)
    organization_user = models.OrganizationUserRole.objects.get(id=organization_user_id)

    if operator == "deactivate":
        organization_user.status = "disactive"
    elif operator == "activate":
        organization_user.status = "active"

    organization_user.last_modifier = current_user._get_current_object()
    organization_user.updated_date = datetime.datetime.now()
    organization_user.last_ip_address = request.headers.get(
        "X-Forwarded-For", request.remote_addr
    )
    organization_user.save()

    print(operator, "user", organization_user.user.first_name)
    return redirect(
        url_for(
            "organizations.view_users",
            organization_id=organization.id,
            role="all",
        )
    )


@module.route("/<organization_id>/logos/add", methods=["GET", "POST"])
@acl.organization_roles_required("staff, admin")
def add_logo(organization_id):
    organization = models.Organization.objects.get(id=organization_id)
    logo = models.CertificateLogo()
    form = forms.organizations.OrganizationLogoForm()

    if not form.validate_on_submit():
        print(form.errors)
        return render_template(
            "/organizations/add-logo.html",
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

    logo.organization = organization
    logo.uploaded_by = current_user._get_current_object()
    logo.uploaded_date = datetime.datetime.now()
    logo.save()

    return redirect(
        url_for("organizations.view_logos", organization_id=organization_id)
    )


@module.route("/<organization_id>/<logo_id>/delete")
@acl.organization_roles_required("admin")
def delete_logo(organization_id, logo_id):
    organization = models.Organization.objects.get(id=organization_id)
    logo = models.CertificateLogo.objects.get(id=logo_id)
    logo.delete()

    return redirect(
        url_for("organizations.view_logos", organization_id=organization_id)
    )
