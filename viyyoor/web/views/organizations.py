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
    organizations = models.Organization.objects(
        status="active",
    )
    return render_template(
        "/organizations/index.html",
        now=datetime.datetime.now,
        organizations=organizations,
    )


@module.route("/<organization_id>")
@acl.organization_roles_required("endorser")
def view(organization_id):
    organization = models.Organization.objects.get(
        id=organization_id,
        status="active",
    )
    logos = models.Logo.objects(organization=organization)
    classes = models.Class.objects(organization=organization, status="active")
    return render_template(
        "/organizations/home.html",
        logos=logos,
        organization=organization,
        classes=classes,
    )


@module.route("/<organization_id>/edit", methods=["GET", "POST"])
@acl.organization_roles_required("admin")
def edit(organization_id):
    organization = models.Organization.objects.get(id=organization_id)
    form = forms.organizations.AdminOrganizationEditForm()

    if not form.validate_on_submit():
        form.name.data = organization.name
        form.description.data = organization.description
        return render_template(
            "/organizations/edit.html", organization=organization, form=form
        )

    form.populate_obj(organization)
    organization.save()

    return redirect(url_for("organizations.view", organization_id=organization_id))


@module.route("/logos/<logo_id>/download/<filename>")
def download_logo(logo_id, filename):
    response = Response()
    response.status_code = 404
    logo = models.Logo.objects.get(id=logo_id)

    if logo:
        response = send_file(
            logo.logo_file,
            download_name=filename,
            mimetype=logo.logo_file.content_type,
        )

    return response


@module.route(
    "/<organization_id>/logos/<logo_id>/set_as_organization_logo", methods=["POST"]
)
@acl.organization_roles_required("admin")
def change_organization_logo(organization_id, logo_id):
    organization = models.Organization.objects.get(id=organization_id)
    old_logo = models.CertificateLogo.objects(
        organization=organization, marked_as_organization_logo=True
    ).first()
    if old_logo:
        old_logo.marked_as_organization_logo = False
        old_logo.last_updated_by = current_user._get_current_object()
        old_logo.updated_date = datetime.datetime.now()
        old_logo.save()

    new_logo = models.Logo.objects.get(id=logo_id)
    new_logo.marked_as_organization_logo = True
    new_logo.last_updated_by = current_user._get_current_object()
    new_logo.updated_date = datetime.datetime.now()
    new_logo.save()

    return redirect(url_for("organizations.view", organization_id=organization.id))


@module.route("/<organization_id>/classes", methods=["GET", "POST"])
@acl.organization_roles_required()
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
@acl.organization_roles_required()
def view_logos(organization_id):
    organization = models.Organization.objects.get(id=organization_id)
    logos = models.CertificateLogo.objects(organization=organization)
    return render_template(
        "/organizations/logos.html",
        organization=organization,
        logos=logos,
    )


@module.route("/<organization_id>/users", methods=["GET", "POST"])
@acl.organization_roles_required()
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
    elif operator == "delete":
        user = organization_user.user
        user.organizations.remove(organization)
        if user.get_current_organization() == organization:
            user.user_setting.current_organization = None
        user.save()
        organization_user.delete()

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


@module.route("/<organization_id>/templates", methods=["GET", "POST"])
@acl.organization_roles_required()
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
