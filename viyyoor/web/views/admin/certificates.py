from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("certificates", __name__, url_prefix="/certificates")


@module.route("/")
@acl.roles_required("admin")
def index():
    return "certificates"


@module.route("/<certificate_id>/delete")
@acl.roles_required("admin")
def delete(user_id):
    certificate = models.Certificate.objects.get(id=user_id)
    certificate.satus = "delete"
    certificate.save()

    return ""
