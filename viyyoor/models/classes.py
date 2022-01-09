import mongoengine as me
import datetime


PARTICIPANT_GROUP = [
    ("participant", "Participant"),
    ("achievement", "Achievement"),
]


class Participant(me.EmbeddedDocument):
    participant_id = me.StringField(required=True, max_length=20)
    first_name = me.StringField(required=True, max_length=256)
    last_name = me.StringField(required=True, max_length=256)
    group = me.StringField(
        required=True,
        choices=PARTICIPANT_GROUP,
    )

    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )


class Endorser(me.EmbeddedDocument):
    endorser_id = me.StringField(
        required=True,
        choices=[
            ("endorser_1", "Endorser 1"),
            ("endorser_2", "Endorser 2"),
            ("endorser_3", "Endorser 3"),
            ("endorser_4", "Endorser 4"),
        ],
    )
    user = me.ReferenceField("User", dbref=True, required=True)
    title = me.StringField(max_length=50)
    first_name = me.StringField(required=True, max_length=256)
    last_name = me.StringField(required=True, max_length=256)

    position = me.StringField()
    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )


class CertificateTemplate(me.EmbeddedDocument):
    name = me.StringField(required=True, max_length=256)
    appreciate_text = me.StringField(required=True)
    template = me.ReferenceField("Template", required=True)
    group = me.StringField(
        required=True,
        choices=PARTICIPANT_GROUP,
    )

    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )


class Class(me.Document):
    meta = {"collection": "classes"}

    name = me.StringField(required=True, max_length=256)
    description = me.StringField()

    participants = me.EmbeddedDocumentListField(Participant)
    endorsers = me.EmbeddedDocumentListField(Endorser)
    issued_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    certificate_templates = me.MapField(
        field=me.EmbeddedDocumentField(CertificateTemplate)
    )

    tags = me.ListField(me.StringField(required=True))

    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    owner = me.ReferenceField("User", dbref=True, required=True)

    status = me.StringField(required=True, default="active")

    def get_participant(self, participant_id: str):
        for p in self.participants:
            if p.participant_id == participant_id:
                return p

        return None

    def get_endorser(self, endorser_id: str):
        for end in self.endorsers:
            if end.endorser_id == endorser_id:
                return end

        return None
