from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

import datetime

from viyyoor import models
from viyyoor.web import acl, forms

module = Blueprint("classes", __name__, url_prefix="/classes")


@module.route("/")
@acl.roles_required("admin")
def index():
    classes = models.Class.objects(status="active")
    return render_template(
        "/admin/classes/index.html",
        classes=classes,
    )


@module.route(
    "/create",
    methods=["GET", "POST"],
    defaults={"class_id": None},
)
@module.route("/<class_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(class_id):
    form = forms.classes.ClassForm()
    class_ = None
    if class_id:
        class_ = models.Class.objects.get(id=class_id)
        form = forms.classes.ClassForm(obj=class_)

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/create-edit.html",
            form=form,
        )

    if not class_id:
        class_ = models.Class()
        class_.owner = current_user._get_current_object()

    form.populate_obj(class_)
    class_.save()

    return redirect(url_for("admin.classes.index"))


@module.route("/<class_id>")
@acl.roles_required("admin")
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template(
        "/admin/classes/view.html",
        class_=class_,
    )


@module.route("/<class_id>/delete")
@acl.roles_required("admin")
def delete(class_id):
    class_ = models.Class.objects.get(id=class_id)
    class_.status = "delete"
    class_.save()

    return redirect(url_for("admin.classes.index"))


@module.route(
    "/<class_id>/endorsers/add",
    methods=["GET", "POST"],
    defaults={"endorser_id": None},
)
@module.route("/<class_id>/endorsers/<endorser_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_or_edit_endorsers(class_id, endorser_id):
    form = forms.classes.EndorserForm()
    endorser = None
    class_ = None
    if class_id:
        class_ = models.Class.objects.get(id=class_id)

        if endorser_id:
            for end in class_.endorsers:
                if end.endorser_id == endorser_id:
                    endorser = end
                    form = forms.classes.ClassForm(obj=end)
                    break

    users = models.User.objects(roles="endorser").order_by("first_name")
    form.user.choices = [
        (str(user.id), f"{user.first_name} {user.last_name}") for user in users
    ]

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/add-or-edit-endorser.html",
            form=form,
            class_=class_,
        )

    is_found_endorser_id = False
    for end in class_.endorsers:
        if end.endorser_id == form.endorser_id.data:
            endorser = end
            is_found_endorser_id = True
            break

    if not is_found_endorser_id:
        endorser = models.Endorser(endorser_id=form.endorser_id.data)
        class_.endorsers.append(endorser)

    endorser.user = models.User.objects.get(id=form.user.data)
    endorser.position = form.position.data
    class_.save()

    return redirect(url_for("admin.classes.add_or_edit_endorsers", class_id=class_.id))


@module.route("/<class_id>/endorsers/<position>/delete", methods=["GET", "POST"])
@acl.roles_required("admin")
def delete_endorser(class_id, position):
    class_ = models.Class.objects.get(id=class_id)

    endorser = None
    for end in class_.endorsers:
        if end.position == position:
            endorser = end
            break

    class_.endorsers.remove(endorser)
    class_.save()

    return redirect(url_for("admin.classes.add_or_edit_endorsers", class_id=class_.id))


@module.route("/<class_id>/paticipants/add", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_participant(class_id, endorser_id):
    class_ = models.Class.objects.get(id=class_id)

    endorser = None
    for end in class_.endorsers:
        if end.position == position:
            endorser = end
            break

    class_.endorsers.remove(endorser)
    class_.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))
