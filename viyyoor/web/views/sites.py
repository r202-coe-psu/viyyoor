from flask import Blueprint, render_template, redirect, url_for
import datetime

from .. import models
from .. import caches

module = Blueprint("site", __name__)


@module.route("/")
@caches.cache.cached(timeout=600)
def index():
    now = datetime.datetime.now()
    class_count = models.Class.objects(status="active").count()
    certificate_count = models.Certificate.objects(status="completed").count()
    return render_template(
        "/sites/index.html",
        class_count=class_count,
        certificate_count=certificate_count,
    )
