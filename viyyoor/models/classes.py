import mongoengine as me
import datetime

class Participant(me.EmbeddedDocument):
    student_id = me.StringField(required=True)
    first_name = me.StringField(required=True)
    last_name = me.StringField(required=True)
    grade = me.StringField(
            required=True,
            choices=[
                'participator',
                'achievement',
                ])

class Endorsee(me.EmbeddedDocument):
    meta = {'collection': 'endorses'}

    order = me.StringField(required=True,
            choices=[
                ('endorsee1', 'Endorsee 1'),
                ('endorsee2', 'Endorsee 2'),
                ('endorsee3', 'Endorsee 3'),
                ('endorsee4', 'Endorsee 4'),
                ])
    user = me.ReferenceField('User', dbref=True, required=True)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)




class Class(me.Document):
    meta = {'collection': 'classes'}

    name = me.StringField(required=True, max_length=255)
    description = me.StringField()

    participants = me.EmbeddedDocumentListField(Participant)
    endorses = me.EmbeddedDocumentListField(Endorsee)

    tags = me.ListField(me.StringField(required=True))

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)

    owner = me.ReferenceField('User', dbref=True, required=True)

    status = me.StringField(required=True, default='active')
