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


class Participant(me.EmbeddedDocument):
    participant_id = me.StringField(required=True, max_length=20)
    title = me.StringField(default="", max_length=50)
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
    title = me.StringField(default="", max_length=50)
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

    def get_certificate(self, participant_id: str):
        from viyyoor import models

        return models.Certificate.objects(
            class_=self, participant_id=participant_id
        ).first()

    def render_certificate(self, participant_id, extension):

        participant = self.get_participant(participant_id)
        certificate_template = self.certificate_templates.get(participant.group)

        if not certificate_template:
            return None

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
            participant_name=(
                f"{participant.title} {participant.first_name} {participant.last_name}"
            ).strip(),
            appreciate_text="".join(appreciate_text),
            module_name=self.name,
            issued_date=self.issued_date.strftime("%B %Y, %-d"),
            validation_url=validation_url,
            validation_qrcode=f"image/png;base64,{qrcode_encoded}",
        )

        for endorser in self.endorsers:
            variables[f"{ endorser.endorser_id }_name"] = (
                f"{endorser.title} { endorser.first_name } { endorser.last_name }"
            ).strip()

            text = [t.strip() for t in endorser.position.split("\n")]
            for i, t in enumerate(text):
                variables[f"{ endorser.endorser_id }_position_{i}"] = t

            signature = endorser.user.get_signature()
            sign_encoded = ""

            if signature:
                sign_encoded = base64.b64encode(signature.file.read()).decode("ascii")
            variables[
                f"{ endorser.endorser_id }_sign"
            ] = f"image/png;base64,{sign_encoded}"

        data = template.render(**variables)

        if extension == "png":
            output = cairosvg.svg2png(bytestring=data.encode())
        elif extension == "pdf":
            output = cairosvg.svg2pdf(bytestring=data.encode())

        image_io = io.BytesIO()
        image_io.write(output)
        image_io.seek(0)

        return image_io
