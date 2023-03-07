from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms

import datetime
import io

from viyyoor import models


def sign_certificates(class_id, issuer_printed_name, issuer_contact_email):
    class_ = models.Class.objects.get(id=class_id)
    certificates = models.Certificate.objects(class_=class_, status="signing")
    now = datetime.datetime.now()
    dc = (
        models.DigitalCertificate.objects(
            status="active", started_date__lte=now, expired_date__gte=now
        )
        .order_by("-id")
        .first()
    )
    if not dc:
        print("Digital Signature is None")
        raise Exception("Digital Singnature not Found")

    for certificate in certificates:
        sign_digital_signature(
            certificate, dc, issuer_printed_name, issuer_contact_email
        )
        certificate.signed_date = datetime.datetime.now()
        certificate.status = "completed"
        certificate.privacy = "public"

        certificate.updated_date = datetime.datetime.now()
        certificate.save()

def sign_digital_signature(
    certificate, dc, issuer_printed_name="", issuer_contact_email="email@email.local"
):
    password = dc.decrypt_password(dc.password)
    dc.file.seek(0)
    p12 = pkcs12.load_key_and_certificates(
        dc.file.read(), password, backends.default_backend()
    )

    reason = "Issued Certificate"

    if issuer_printed_name:
        reason = f"Issued Certificate by {issuer_printed_name}"

    now = datetime.datetime.utcnow()
    # date_str = now.strftime("D:%Y%m%d%H%M%S+00'00'")
    date_str = now.strftime("%Y%m%d%H%M%S+00'00'")
    box = [25, 0, 350, 5]
    dct = {
        "aligned": 0,
        "sigflags": 3,
        "sigflagsft": 132,
        "sigpage": 0,
        "sigbutton": True,
        "sigfield": "Signature",
        "auto_sigfield": True,
        "sigandcertify": True,
        "signaturebox": box,
        "signature": issuer_printed_name,
        # "text": {"textalign": "center", "fontsize": 5},
        "text": {"textalign": "left", "fontsize": 5},
        "contact": issuer_contact_email,
        "location": "Hat Yai, Thailand",
        "signingdate": date_str,
        "reason": reason,
    }

    signed_file = sign_cms(certificate.file, p12, dct)
    certificate.file.replace(signed_file)
    certificate.ca_download_url = dc.ca_download_url
    certificate.save()


def sign_cms(document_fp, p12, dct):
    datau = document_fp.read()
    datas = cms.sign(datau, dct, p12[0], p12[1], p12[2], "sha256")
    fileio = io.BytesIO()
    fileio.write(datau)
    fileio.write(datas)
    fileio.seek(0)

    return fileio
