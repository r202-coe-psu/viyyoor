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
import PIL
import copy
import io

from viyyoor import models
from viyyoor.web import acl, forms
from viyyoor.web.views import organizations

from . import certificate_quotas

module = Blueprint("organizations", __name__, url_prefix="/organizations")


@module.route("/")
@acl.roles_required("admin")
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


@module.route("/<organization_id>/logos", methods=["GET", "POST"])
@acl.organization_roles_required("admin", "endorser", "staff")
def view_logos(organization_id):
    return organizations.view_logos(organization_id)


@module.route(
    "/<organization_id>/logos/add", methods=["GET", "POST"], defaults={"logo_id": ""}
)
@module.route(
    "/<organization_id>/logos/<logo_id>/edit",
    methods=["GET", "POST"],
)
@acl.organization_roles_required("staff", "admin")
def add_or_edit_logo(organization_id, logo_id):
    return organizations.add_or_edit_logo(organization_id, logo_id)


@module.route("/<organization_id>/<logo_id>/delete")
@acl.organization_roles_required("admin")
def delete_logo(organization_id, logo_id):
    return organizations.delete_logo(organization_id, logo_id)


@module.route("/<organization_id>/certificates")
@acl.organization_roles_required("admin", "staff")
def view_certificates(organization_id):
    return organizations.view_certificates(organization_id)
