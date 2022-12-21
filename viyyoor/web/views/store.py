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

module = Blueprint("store", __name__, url_prefix="/store")


@module.route("/")
def index():
    organizations = models.Organization.objects()
    templates = models.Template.objects(
        status="active",
    )

    return render_template(
        "/store/index.html",
        organizations=organizations,
        templates=templates,
    )
