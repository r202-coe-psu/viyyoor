import datetime

import io
import cairosvg
import qrcode
import base64
import copy

import PIL

from lxml import etree

from jinja2 import Environment, PackageLoader, select_autoescape, Template
from viyyoor import models

from viyyoor.utils import digital_signature_utils, email_utils

PX_TO_MM = 0.2645833333
LOGO_SPACE = 2
DY_ENDORSER_POSSITION = 5
DY_CLASS_NAME = 10
DY_AUTHENTICITY = 3
DY_ORGANIZATION_NAME = 10
DY_DECLARATION_TEXT = 10
DY_CERTIFICATE_NAME = 10
DY_PARTICIPANT_NAME = 10
DY_ACADEMY = 5
DY_CERTIFICATE_TEXT = 8
DY_VALIDATION_URL = 4
DY_CLASS_DATE = 10
DY_REMARK = 4


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


def create_certificate_endorsement(class_, user, ip_address, config):
    for certificate in class_.get_certificates():
        if certificate.status != "prerelease":
            continue

        # Endorse Certifcate after prepair
        for endorser_id, endorser in class_.endorsers.items():
            if endorser.endorse_requirement == "required":
                continue

            endorsement = models.Endorsement(
                endorser=endorser.user,
                ip_address=ip_address,
                remark=f"this endorser is current not required to endorse certificate",
            )

            if endorser.endorser_id not in certificate.endorsements:
                certificate.endorsements[endorser.endorser_id] = endorsement

            check_approval = True
            for key, endorser in certificate.class_.endorsers.items():
                if endorser.endorser_id not in certificate.endorsements:
                    check_approval = False
                elif (
                    endorser.endorser_id in certificate.endorsements
                    and endorser.user
                    != certificate.endorsements[endorser.endorser_id].endorser
                ):
                    check_approval = False

                if not check_approval:
                    break

            if check_approval:
                certificate.status = "signing"

            certificate.updated_date = datetime.datetime.now()
            certificate.save()

    digital_signature_utils.sign_certificates(class_.id, config)


def add_certificate_logo(et, class_):
    page_width = 0
    element = et.getroot()
    page_width_str = element.attrib.get("width")
    if "mm" in page_width_str:
        page_width_str = page_width_str.replace("mm", "")
        page_width = int(page_width_str)

    cert_logo_element = element.find(".//*[@id='cert-logo']")

    if cert_logo_element is None:
        return

    logo_template_element = cert_logo_element[0]
    logo_template_height = float(logo_template_element.attrib.get("height"))

    cert_logo_element.remove(logo_template_element)

    logo_elements = []
    total_width = 0

    for idx, certificate_logo in enumerate(class_.certificate_logos):
        img = PIL.Image.open(certificate_logo.logo.logo_file)
        if not img:
            continue

        logo_width, logo_height = img.size

        ratio = logo_height / (logo_template_height / PX_TO_MM)

        new_logo_size = (
            int(round(logo_width / ratio)),
            int(round(logo_height / ratio)),
        )

        resized_logo_img = img

        if logo_height > 500:
            resize_ratio = logo_height / 500
            new_logo_resize = (
                int(round(logo_width / resize_ratio)),
                int(round(logo_height / resize_ratio)),
            )
            resized_logo_img = img.resize(new_logo_resize, PIL.Image.ANTIALIAS)

        new_element = copy.deepcopy(logo_template_element)
        new_element.set("width", str(new_logo_size[0] * PX_TO_MM))
        new_element.set("height", str(new_logo_size[1] * PX_TO_MM))
        new_element.set("id", f"logo-{idx}")

        buffered = io.BytesIO()
        resized_logo_img.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        new_element.set(
            "{http://www.w3.org/1999/xlink}href",
            f"data:image/png;base64,{base64_image}",
        )

        logo_elements.append(new_element)
        total_width += new_logo_size[0] * PX_TO_MM + LOGO_SPACE

    diff_page_width = (page_width - total_width + LOGO_SPACE) / 2

    start_logo_x = diff_page_width

    for element in logo_elements:
        element.set("x", str(start_logo_x))
        cert_logo_element.append(element)

        start_logo_x += float(element.get("width")) + LOGO_SPACE


def prepare_template(
    class_,
    et,
    required_signature=True,
):
    add_certificate_logo(et, class_)
    add_endorsers(et, class_, required_signature)


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


def add_qrcode(et, validation_url):
    base64_qrcode_image = render_qrcode(validation_url)
    element = et.getroot()

    qrcode_element = element.find(".//*[@id='validation_qrcode']")

    if qrcode_element is not None:
        qrcode_element.set(
            "{http://www.w3.org/1999/xlink}href",
            f"data:image/png;base64,{base64_qrcode_image}",
        )


def add_multiline(et, element_name, print_text, line_dy=4):
    element = et.getroot()
    parent_element = element.find(f".//*[@id='{element_name}']")
    if parent_element is None:
        return

    template_element = parent_element[0]
    if "y" in template_element.attrib:
        template_element.attrib.pop("y")

    for element in parent_element.getchildren():
        parent_element.remove(element)

    for possition_id, text in enumerate(print_text.split("\n")):
        pos_element = copy.deepcopy(template_element)
        pos_element.set("id", f"{element_name}_{possition_id}")
        pos_element.text = text.strip()
        if possition_id != 0:
            pos_element.set("dy", str(line_dy))
        parent_element.append(pos_element)


def add_endorsers(et, class_, required_signature=True):
    ENDOSER_NUMS = 5
    element = et.getroot()
    for idx in range(1, ENDOSER_NUMS + 1):
        endorser_element = element.find(f".//*[@id='endorser_{idx}']")
        if endorser_element is None:
            continue

        endorser = class_.endorsers.get(f"endorser_{idx}")
        if not endorser:
            parent = endorser_element.getparent()
            parent.remove(endorser_element)

            endorser_sign_element = element.find(f".//*[@id='endorser_{idx}_sign']")
            if endorser_sign_element is not None:
                parent = endorser_sign_element.getparent()
                parent.remove(endorser_sign_element)
            continue

        signature = endorser.user.get_signature()
        sign_encoded = ""
        if signature and required_signature:
            if signature.file:
                sign_encoded = base64.b64encode(signature.file.read()).decode("utf-8")

        endorser_sign_element = element.find(f".//*[@id='endorser_{idx}_sign']")
        if endorser_sign_element is not None:
            if sign_encoded:
                endorser_sign_element.set(
                    "{http://www.w3.org/1999/xlink}href",
                    f"data:{signature.file.content_type};base64,{sign_encoded}",
                )
            else:
                parent = endorser_sign_element.getparent()
                parent.remove(endorser_sign_element)

        endorser_name_element = element.find(f".//*[@id='endorser_{idx}_name']")
        if endorser_name_element is None:
            continue

        endorser_name_element.text = f"({endorser.name})"
        # endorser_element.append(endorser_name_element)

        template_element = element.find(f".//*[@id='endorser_{idx}_position']")
        template_element.attrib.pop("y")
        endorser_element.remove(template_element)

        for possition_id, text in enumerate(endorser.position.split("\n")):
            endorser_pos_element = copy.deepcopy(template_element)
            endorser_pos_element.set("id", f"endorser_{idx}_position_{possition_id}")
            endorser_pos_element.text = text
            endorser_pos_element.set("dy", str(DY_ENDORSER_POSSITION))
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

    et = etree.parse(certificate_template.template.template_file)

    prepare_template(class_, et, required_signature)

    certificate = class_.get_certificate_by_participant_id(participant_id)

    validation_url = validated_url_template.format(certificate_id="test")
    if certificate:
        validation_url = validated_url_template.format(certificate_id=certificate.id)

    certificate_template = class_.certificate_templates.get(participant.group)

    class_date_text = class_.class_date_text
    if not class_date_text:
        class_date_text = class_.started_date.strftime("%-d %B %Y")
        if class_.started_date != class_.ended_date:
            if (
                class_.started_date.year == class_.ended_date.year
                and class_.started_date.month == class_.ended_date.month
            ):
                class_date_text = "{sdate} - {edate} {month} {year}".format(
                    sdate=class_.started_date.strftime("%-d"),
                    edate=class_.ended_date.strftime("%-d"),
                    month=class_.ended_date.strftime("%B"),
                    year=class_.ended_date.year,
                )
            else:
                class_date_text += " - " + class_.ended_date.strftime("%-d %B %Y")

    add_qrcode(et, validation_url)

    render_parameters = [
        ("class_name", class_.printed_name, DY_CLASS_NAME),
        ("authenticity", class_.organization.authenticity_text, DY_AUTHENTICITY),
        (
            "organization_name",
            certificate_template.organization_name,
            DY_ORGANIZATION_NAME,
        ),
        (
            "declaration_text",
            certificate_template.declaration_text,
            DY_DECLARATION_TEXT,
        ),
        ("certificate_name", certificate_template.name, DY_CERTIFICATE_TEXT),
        ("participant_name", participant.name.strip(), DY_PARTICIPANT_NAME),
        ("academy", participant.organization.strip(), DY_ACADEMY),
        (
            "certificate_text",
            certificate_template.certificate_text,
            DY_CERTIFICATE_TEXT,
        ),
        ("validation_url", validation_url, DY_VALIDATION_URL),
        ("class_date", class_date_text, DY_CLASS_DATE),
        ("remark", certificate_template.remark, DY_REMARK),
    ]
    for k, v, dy in render_parameters:
        # print(type(certificate_template))
        add_multiline(
            et,
            k,
            v,
            certificate_template.template.parameters.get(f"dy_{k}", dy),
        )

    data = etree.tostring(et.getroot(), encoding="utf-8", method="xml").decode("utf-8")

    template = Template(data)

    variables = dict(issued_date=class_.issued_date.strftime("%-d %B %Y"))

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
            printed_text.append(f'<tspan dy="{10*(i+1)}">{t.strip()}</tspan>')
        variables[k] = "".join(printed_text)

    data = template.render(**variables)
    # print(variables)

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
