from flask import redirect, url_for, request
from flask_login import current_user, LoginManager, login_url
from werkzeug.exceptions import Forbidden
from . import models

from functools import wraps

login_manager = LoginManager()


def init_acl(app):
    login_manager.init_app(app)

    @app.errorhandler(401)
    def unauthorized(e):
        return unauthorized_callback()

    @app.errorhandler(403)
    def forbidden(e):
        return "You don't have permission."


def roles_required(*roles):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                raise Forbidden()

            for role in roles:
                if role in current_user.roles:
                    return func(*args, **kwargs)
            raise Forbidden()

        return wrapped

    return wrapper


def organization_roles_required(*roles):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                raise Forbidden()

            # bypass admin to access any organization
            if "admin" in current_user.roles:
                return func(*args, **kwargs)

            try:
                organization_id = request.view_args.get("organization_id")
                organization = models.Organization.objects.get(id=organization_id)
                organization_role = (
                    models.OrganizationUserRole.objects(
                        user=current_user,
                        organization=organization,
                        status="active",
                    )
                    .first()
                    .role
                )
            except:
                organization_role = None

            for role in roles:
                if role in organization_role:
                    return func(*args, **kwargs)

            raise Forbidden()

        return wrapped

    return wrapper


@login_manager.user_loader
def load_user(user_id):
    user = models.User.objects.with_id(user_id)
    return user


@login_manager.unauthorized_handler
def unauthorized_callback():
    if request.method == "GET":
        response = redirect(login_url("accounts.login", request.url))
        return response

    return redirect(url_for("accounts.login"))
