import mongoengine as me
import bson
import datetime

from jinja2 import Environment, PackageLoader, select_autoescape, Template

import io
import cairosvg
import qrcode
import base64

PARTICIPANT_GROUP = [
    ("participant", "Participant"),
    ("achievement", "Achievement"),
    ("winner", "Winner"),
    ("first_runner_up", "First Runner-up"),
    ("second_runner_up", "Second Runner-up"),
    ("honorable_mention_prize", "Honorable Mention Prize"),
    ("advisor", "Advisor"),
]

ENDORSER_POSITIONS = [
    ("endorser_1", "Endorser 1"),
    ("endorser_2", "Endorser 2"),
    ("endorser_3", "Endorser 3"),
    ("endorser_4", "Endorser 4"),
]


class Participant(me.EmbeddedDocument):
    id = me.ObjectIdField(required=True, default=bson.ObjectId)
    common_id = me.StringField(required=True, max_length=20)
    name = me.StringField(required=True, max_length=256)
    email = me.StringField(max_length=200)
    group = me.StringField(
        required=True,
        choices=PARTICIPANT_GROUP,
    )
    organization = me.StringField(max_length=256, default="")

    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    extra = me.DictField()


class Endorser(me.EmbeddedDocument):
    endorser_id = me.StringField(
        required=True,
        choices=ENDORSER_POSITIONS,
    )
    user = me.ReferenceField("User", dbref=True, required=True)
    name = me.StringField(required=True, max_length=256)

    position = me.StringField()
    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )

    def get_signature(self):
        from .signatures import Signature

        return Signature.objects(owner=self.user).order_by("-id").first()


class CertificateTemplate(me.EmbeddedDocument):
    name = me.StringField(required=True, max_length=256)
    certificate_text = me.StringField(required=True)
    declaration_text = me.StringField(default="")
    class_date = me.StringField(max_length=256, default="")

    organization_name = me.StringField(default="")
    group = me.StringField(
        required=True,
        choices=PARTICIPANT_GROUP,
    )

    template = me.ReferenceField("Template", required=True)

    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )


class CertificateLogo(me.EmbeddedDocument):
    logo = me.ReferenceField("Logo", dbref=True, required=True)
    order = me.IntField(required=True, default=0)
    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )


class Class(me.Document):
    meta = {"collection": "classes"}

    name = me.StringField(required=True, max_length=256)
    printed_name = me.StringField(required=True, max_length=256)
    description = me.StringField()

    participants = me.MapField(field=me.EmbeddedDocumentField(Participant))
    endorsers = me.MapField(field=me.EmbeddedDocumentField(Endorser))
    instructors = me.ListField(me.StringField())

    issued_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    certificate_templates = me.MapField(
        field=me.EmbeddedDocumentField(CertificateTemplate)
    )
    certificate_logos = me.EmbeddedDocumentListField("CertificateLogo")

    tags = me.ListField(me.StringField(required=True))

    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    owner = me.ReferenceField("User", dbref=True, required=True)

    status = me.StringField(required=True, default="active")

    def get_participant(self, pid):
        if type(pid) is not str:
            pid = str(pid)

        return self.participants.get(pid, None)

    def get_participants_with_participant_id(self, participant_id: str):
        participants = []
        for p in self.participants:
            if p.participant_id == participant_id:
                participants.append(p)

        return participants

    def get_endorser(self, endorser_id: str):
        return self.endorsers.get(endorser_id, None)

    def get_endorsers_by_user(self, user):
        endorsers = []
        for key, end in self.endorsers.items():
            if end.user == user:
                endorsers.append(end)

        return endorsers

    def get_certificates(self):
        from viyyoor import models

        return models.Certificate.objects(class_=self)

    def get_certificate(self, participant_id):
        from viyyoor import models

        if not participant_id:
            return None

        return models.Certificate.objects(
            class_=self, participant_id=participant_id
        ).first()

    def get_certificates_endorsed_by_user(self, user):
        from viyyoor import models

        endorsed_query = dict()
        for ep in ENDORSER_POSITIONS:
            endorsed_query[f"endorsements__{ep[0]}__endorser"] = user

        query_obj = None
        for k, v in endorsed_query.items():
            if query_obj:
                query_obj = query_obj | me.Q(**{k: v})
            else:
                query_obj = me.Q(**{k: v})

        certificates = models.Certificate.objects(
            query_obj,
            class_=self,
        )

        return certificates

    def get_completed_certificates(self):
        from viyyoor import models

        completed_certificates = models.Certificate.objects(
            class_=self, status="completed"
        )

        return completed_certificates

    def get_authenticity_text(self):
        from flask import current_app

        return current_app.config.get("DEFAULT_AUTHENTICITY_TEXT", "")
