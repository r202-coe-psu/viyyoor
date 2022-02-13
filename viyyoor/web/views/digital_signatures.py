from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms
import datetime
import io

from viyyoor import models


def sign_certificates(class_):
    certificates = models.Certificate.objects(class_=class_, status="signing")
    for certificate in certificates:
        dc = models.DigitalCertificate.objects(status="active").order_by("-id").first()
        sign_digital_signature(certificate, dc)
        certificate.signed_date = datetime.datetime.now()
        certificate.status = "completed"
        certificate.privacy = "public"

        certificate.updated_date = datetime.datetime.now()
        certificate.save()


def sign_digital_signature(certificate, dc, reason=""):

    password = dc.decrypt_password(dc.password)
    p12 = pkcs12.load_key_and_certificates(
        dc.file.read(), password, backends.default_backend()
    )

    if not reason.strip():
        reason = "Issued Certificate by Department of Computer Engineering"

    now = datetime.datetime.utcnow()
    date_str = now.strftime("D:%Y%m%d%H%M%S+00'00'")
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
        "signature": "Department of Computer Engineering, Faculty of Engineering, Prince of Songkla University",
        # "text": {"textalign": "center", "fontsize": 5},
        "text": {"textalign": "left", "fontsize": 5},
        "contact": "admin@coe.psu.ac.th",
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
