import mongoengine as me
import datetime


class Participant(me.EmbeddedDocument):
    student_id = me.StringField(required=True)
    first_name = me.StringField(required=True)
    last_name = me.StringField(required=True)
    grade = me.StringField(
        required=True,
        choices=[
            "participator",
            "achievement",
        ],
    )


class Endorser(me.EmbeddedDocument):

    position = me.StringField(
        required=True,
        choices=[
            ("endorser1", "Endorser 1"),
            ("endorser2", "Endorser 2"),
            ("endorser3", "Endorser 3"),
            ("endorser4", "Endorser 4"),
        ],
    )
    user = me.ReferenceField("User", dbref=True, required=True)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )


class Class(me.Document):
    meta = {"collection": "classes"}

    name = me.StringField(required=True, max_length=255)
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
