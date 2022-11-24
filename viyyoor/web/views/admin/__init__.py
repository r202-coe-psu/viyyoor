from flask import Blueprint, render_template, redirect, url_for
import datetime

from viyyoor import models
from viyyoor.web import acl

module = Blueprint("admin", __name__, url_prefix="/admin")


@module.route("/")
@acl.roles_required("admin")
def index():
    organizations = models.Organization.objects()
    classes = models.Class.objects()
    templates = models.Template.objects()
    users = models.User.objects()

    return render_template(
        "/admin/index.html",
        organizations=organizations,
        classes=classes,
        templates=templates,
        users=users
    )
