import mongoengine as me
import datetime

from jinja2 import Environment, PackageLoader, select_autoescape, Template

import io
import cairosvg
import qrcode
import base64

PARTICIPANT_GROUP = [
    ("participant", "Participant"),
    ("achievement", "Achievement"),
]

ENDORSER_POSITIONS = [
    ("endorser_1", "Endorser 1"),
    ("endorser_2", "Endorser 2"),
    ("endorser_3", "Endorser 3"),
    ("endorser_4", "Endorser 4"),
]


class Participant(me.EmbeddedDocument):
    participant_id = me.StringField(required=True, max_length=20)
    name = me.StringField(required=True, max_length=256)
    group = me.StringField(
        required=True,
        choices=PARTICIPANT_GROUP,
    )

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
    printed_name = me.StringField(required=True, max_length=256)
    description = me.StringField()

    participants = me.MapField(field=me.EmbeddedDocumentField(Participant))
    endorsers = me.MapField(field=me.EmbeddedDocumentField(Endorser))
    instructors = me.ListField(me.StringField())

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
        return self.participants.get(participant_id, None)

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

    def get_certificate(self, participant_id: str):
        from viyyoor import models

        return models.Certificate.objects(
            class_=self, participant_id=participant_id
        ).first()

    def render_certificate(self, participant_id, extension, required_signature=True):

        participant = self.get_participant(participant_id)
        certificate_template = self.certificate_templates.get(participant.group)

        if not certificate_template:
            return None

        certificate_template.template.file.seek(0)
        data = certificate_template.template.file.read().decode()
        template = Template(data)

        text = [t.strip() for t in certificate_template.appreciate_text.split("\n")]

        appreciate_text = []
        if len(text) > 0:
            appreciate_text = [f"<tspan>{text[0]}</tspan>"]
            appreciate_text.extend(
                [f'<tspan x="50%" dy="10">{t.strip()}</tspan>' for t in text[1:]]
            )

        validation_url = ""
        certificate = self.get_certificate(participant_id)

        if certificate:
            validation_url = certificate.get_validation_url()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=5,
            border=2,
        )
        qr.add_data(validation_url)
        qr.make(fit=True)

        qrcode_image = qr.make_image().convert("RGB")

        qrcode_io = io.BytesIO()
        qrcode_image.save(qrcode_io, "PNG", quality=100)
        qrcode_encoded = base64.b64encode(qrcode_io.getvalue()).decode("ascii")

        variables = dict(
            certificate_name=certificate_template.name,
            participant_name=participant.name.strip(),
            appreciate_text="".join(appreciate_text),
            class_name=self.printed_name,
            issued_date=self.issued_date.strftime("%B %Y, %-d"),
            validation_url=validation_url,
            validation_qrcode=f"image/png;base64,{qrcode_encoded}",
        )

        variables.update(participant.extra)

        for key, endorser in self.endorsers.items():
            variables[f"{ endorser.endorser_id }_name"] = endorser.name.strip()

            text = [t.strip() for t in endorser.position.split("\n")]
            for i, t in enumerate(text):
                variables[f"{ endorser.endorser_id }_position_{i}"] = t

            signature = endorser.user.get_signature()

            sign_encoded = ""
            if signature and required_signature:
                sign_encoded = base64.b64encode(signature.file.read()).decode("ascii")

            variables[
                f"{ endorser.endorser_id }_sign"
            ] = f"image/png;base64,{sign_encoded}"

        data = template.render(**variables)

        if extension == "png":
            output = cairosvg.svg2png(bytestring=data.encode())
        elif extension == "pdf":
            output = cairosvg.svg2pdf(bytestring=data.encode())
        elif extension == "svg":
            output = data.encode()

        image_io = io.BytesIO()
        image_io.write(output)
        image_io.seek(0)

        return image_io
