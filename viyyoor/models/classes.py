import mongoengine as me
import datetime


class Participant(me.EmbeddedDocument):
    participant_id = me.StringField(required=True, max_length=20)
    first_name = me.StringField(required=True, max_length=256)
    last_name = me.StringField(required=True, max_length=256)
    group = me.StringField(
        required=True,
        choices=[
            ("participant", "Participant"),
            ("achievement", "Achievement"),
        ],
    )

    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )


class Endorser(me.EmbeddedDocument):

    endorser_id = me.StringField(
        required=True,
        choices=[
            ("endorser1", "Endorser 1"),
            ("endorser2", "Endorser 2"),
            ("endorser3", "Endorser 3"),
            ("endorser4", "Endorser 4"),
        ],
    )
    user = me.ReferenceField("User", dbref=True, required=True)
    position = me.StringField(max_length=256)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )
    last_updated_by = me.ReferenceField("User", dbref=True, required=True)


class Class(me.Document):
    meta = {"collection": "classes"}

    name = me.StringField(required=True, max_length=256)
    description = me.StringField()

    participants = me.EmbeddedDocumentListField(Participant)
    endorsers = me.EmbeddedDocumentListField(Endorser)

    tags = me.ListField(me.StringField(required=True))

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
