from flask import Blueprint, render_template
from flask_login import login_required, current_user

from viyyoor import models
import mongoengine as me

import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")
subviews = []


def index_admin():
    now = datetime.datetime.now()
    endorser_positions = models.classes.ENDORSER_POSITIONS
    # queries = {
    #     f"endorsers__{ep[0]}__user": current_user._get_current_object()
    #     for ep in endorser_positions
    # }
    # print("q", queries)
    classes_set = set()
    for ep in endorser_positions:
        queries = {f"endorsers__{ep[0]}__user": current_user._get_current_object()}
        sub_classes = models.Class.objects(**queries)
        classes_set.update(sub_classes)

    classes = list(classes_set)
    endorses_classes = models.Certificate.objects(
        status="prerelease", class___in=classes
    ).distinct(field="class_")

    endorsed_classes = models.Certificate.objects(
        status="completed", class___in=classes
    ).distinct(field="class_")

    return render_template(
        "/dashboard/index-admin.html",
        now=datetime.datetime.now(),
        endorses_classes=endorses_classes,
        endorsed_classes=endorsed_classes,
    )


def index_user():
    certificates = models.Certificate.objects(
        participant_id=current_user.username
    ).order_by("-id")
    now = datetime.datetime.now()
    return render_template(
        "/dashboard/index-user.html",
        now=datetime.datetime.now(),
        certificates=certificates,
    )


@module.route("/")
@login_required
def index():
    user = current_user._get_current_object()
    if "admin" in user.roles or "endorser" in user.roles:
        return index_admin()

    return index_user()
