from flask import Blueprint, render_template
from flask_login import login_required, current_user

from viyyoor import models
import mongoengine as me

import datetime

module = Blueprint('dashboard', __name__, url_prefix='/dashboard')
subviews = []


def index_admin():
    now = datetime.datetime.now()
    return render_template('/dashboard/index-admin.html',
                           now=datetime.datetime.now(),
                           )


def index_user():
    now = datetime.datetime.now()
    return render_template('/dashboard/index-user.html',
                           now=datetime.datetime.now(),
                           )


@module.route('/')
@login_required
def index():
    user = current_user._get_current_object()
    if 'admin' in user.roles:
        return index_admin()
    
    return index_user()
