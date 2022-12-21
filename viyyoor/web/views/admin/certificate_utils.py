import datetime


import io
import cairosvg
import qrcode
import base64
import copy

from defusedxml import ElementTree

from jinja2 import Environment, PackageLoader, select_autoescape, Template
from viyyoor import models


PX_TO_MM = 0.2645833333
LOGO_SPACE = 2
ENDORSER_POSSITION_DY = 5


def create_certificates(
    class_,
    user,
    validated_url_template="http://localhost/certificates/{certificate_id}",
):
    for key, participant in class_.participants.items():
        certificate = models.Certificate.objects(
            class_=class_, participant_id=participant.id
        ).first()

        if certificate and certificate.status != "prepare":
            continue

        if not certificate:
            certificate = models.Certificate(
                class_=class_,
                participant_id=participant.id,
                common_id=participant.common_id,
            )
            certificate.last_updated_by = user
            certificate.issuer = user
            certificate.save()
            certificate.file.put(
                render_certificate(
                    class_,
                    participant.id,
                    "pdf",
                    validated_url_template=validated_url_template,
                )
            )

        else:
            certificate.file.replace(
                render_certificate(
                    class_,
                    participant.id,
                    "pdf",
                    validated_url_template=validated_url_template,
                )
            )

        certificate.validated_url = validated_url_template.format(
            certificate_id=certificate.id
        )
        certificate.updated_date = datetime.datetime.now()
        certificate.issued_date = class_.issued_date
        certificate.last_updated_by = user
        certificate.issuer = user
        certificate.status = "prerelease"
        certificate.privacy = "prerelease"
        certificate.save()


def add_certificate_logo(element, class_):

    page_width = 0
    page_width_str = element.attrib.get("width")
    if "mm" in page_width_str:
        page_width_str = page_width_str.replace("mm", "")
        page_width = int(page_width_str)

    cert_logo_element = element.find(".//*[@id='cert-logo']")

    if not cert_logo_element:
        return element

    logo_template_element = cert_logo_element[0]
    logo_template_height = float(logo_template_element.attrib.get("height"))

    cert_logo_element.remove(logo_template_element)

    logo_elements = []
    total_width = 0

    for idx, certificate_log in enumerate(class_.certificate_logs):
        img = Image.open(certificate_log.logo)
        if not img:
            continue

        logo_width, logo_height = img.size

        ratio = logo_height / (logo_template_height / PX_TO_MM)

        new_logo_size = (
            int(round(logo_width / ratio)),
            int(round(logo_height / ratio)),
        )

        scal_logo_img = img.resize(new_logo_size)

        new_element = copy.deepcopy(logo_template)
        new_element.set("width", str(new_logo_size[0] * PX_TO_MM))
        new_element.set("height", str(new_logo_size[1] * PX_TO_MM))
        new_element.set("id", f"logo-{idx}")

        buffered = io.BytesIO()
        ximg.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        new_element.set(
            "{http://www.w3.org/1999/xlink}href", f"data:image/png;base64,{img_str}"
        )

        logo_elements.append(new_element)
        total_width += new_logo_size[0] * PX_TO_MM + LOGO_SPACE

    diff_page_width = (page_width - total_width + LOGO_SPACE) / 2

    start_logo_x = diff_page_width

    for element in logo_elements:
        element.set("x", str(start_logo_x))
        cert_logo_et.append(element)

        start_logo_x += float(element.get("width")) + LOGO_SPACE

    return element


def prepare_template(
    class_,
    root,
    required_signature=True,
):

    element = add_certificate_logo(root, class_)
    element = add_endorsers(element, class_, required_signature)

    return element


def render_qrcode(validation_url):
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
    return base64.b64encode(qrcode_io.getvalue()).decode("utf-8")


def add_qrcode(element, validation_url):
    base64_qrcode_image = render_qrcode(validation_url)

    qrcode_element = element.find(".//*[@id='validation_qrcode']")

    if qrcode_element is not None:
        qrcode_element.set(
            "{http://www.w3.org/1999/xlink}href",
            f"data:image/png;base64,{base64_qrcode_image}",
        )

    return element


def add_endorsers(element, class_, required_signature=True):

    ENDOSER_NUMS = 5
    for idx in range(1, ENDOSER_NUMS + 1):
        endorser_element = element.find(f".//*[@id='endorser_{idx}']")
        if not endorser_element:
            continue

        endorser = class_.endorsers.get(f"endorser_{idx}")
        if not endorser:
            element.remove(endorser_element)

            endorser_sign_element = element.find(f".//*[@id='endorser_{idx}_sign']")
            if endorser_sign_element:
                element.remove(endorser_sign_element)

        signature = endorser.user.get_signature()
        sign_encoded = ""
        if signature and required_signature:
            sign_encoded = base64.b64encode(signature.file.read()).decode("utf-8")

        endorser_sign_element = element.find(f".//*[@id='endorser_{idx}_sign']")
        if endorser_sign_element is not None:
            endorser_sign_element.set(
                "{http://www.w3.org/1999/xlink}href",
                f"data:{signature.file.content_type};base64,{sign_encoded}",
            )

        template_element = endorser_element[0]
        template_element.attrib.pop("y")
        endorser_element.remove(template_element)

        endorser_name_element = copy.deepcopy(template_element)
        endorser_name_element.text = f"({endorser.name})"
        endorser_element.append(endorser_name_element)

        for possition_id, text in enumerate(endorser.position.split("\n")):
            endorser_pos_element = copy.deepcopy(template_element)
            endorser_pos_element.set("id", f"endorser_{idx}_position_{possition_id}")
            endorser_pos_element.text = text
            endorser_pos_element.set("dy", str(ENDORSER_POSSITION_DY))
            endorser_element.append(endorser_pos_element)
    return element


def render_certificate(
    class_,
    participant_id,
    extension,
    required_signature=True,
    validated_url_template="https://localhost/certificates/{certificate_id}",
):

    participant = class_.get_participant(participant_id)

    certificate_template = class_.certificate_templates.get(participant.group)

    if not certificate_template:
        return None

    certificate_template.template.template_file.seek(0)

    et = ElementTree.parse(certificate_template.template.template_file)
    root = et.getroot()

    element = prepare_template(class_, root, required_signature=True)

    certificate = class_.get_certificate(participant_id)

    validation_url = validated_url_template.format(certificate_id="test")
    if certificate:
        validation_url = validated_url_template.format(certificate_id=certificate.id)

    element = add_qrcode(root, validation_url)
    data = ElementTree.tostring(element, encoding="utf-8", method="xml").decode("utf-8")

    template = Template(data)

    certificate_template = class_.certificate_templates.get(participant.group)
    text = [t.strip() for t in certificate_template.certificate_text.split("\n")]

    certificate_text = []
    if len(text) > 0:
        certificate_text = [f"<tspan>{text[0]}</tspan>"]
        certificate_text.extend(
            [f'<tspan x="50%" dy="10">{t.strip()}</tspan>' for t in text[1:]]
        )

    class_date = class_.started_date.strftime("%-d %B %Y")
    if class_.started_date != class_.ended_date:
        if (
            class_.started_date.year == class_.ended_date.year
            and class_.started_date.month == class_.ended_date.month
        ):
            class_date = "{sdate} - {edate} {month} {year}".format(
                sdate=class_.started_date.strftime("%-d"),
                edate=class_.ended_date.strftime("%-d"),
                month=class_.ended_date.strftime("%B"),
                year=class_.ended_date.year,
            )
        else:
            class_date += " - " + class_.ended_date.strftime("%-d %B %Y")
    variables = dict(
        certificate_name=certificate_template.name,
        participant_name=participant.name.strip(),
        certificate_text="".join(certificate_text),
        class_name=class_.printed_name,
        issued_date=class_.issued_date.strftime("%-d %B %Y"),
        class_date=class_date,
        validation_url=validation_url,
    )

    for k, v in participant.extra.items():
        if type(v) is not str:
            variables[k] = v
            continue

        text = [t.strip() for t in v.split("\n")]

        if len(text) == 0:
            continue

        if len(text) == 1:
            variables[k] = text[0]
            continue

        printed_text = [f"<tspan>{text[0]}</tspan>"]
        for i, t in enumerate(text[1:]):
            printed_text.append(f'<tspan x="50%" dy="{10*(i+1)}">{t.strip()}</tspan>')
        variables[k] = "".join(printed_text)

    data = template.render(**variables)

    if extension == "png":
        output = cairosvg.svg2png(bytestring=data.encode())
    elif extension == "pdf":
        output = cairosvg.svg2pdf(bytestring=data.encode(), dpi=100)
    elif extension == "svg":
        output = data.encode()

    image_io = io.BytesIO()
    image_io.write(output)
    image_io.seek(0)

    return image_io
