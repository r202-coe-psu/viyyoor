from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms
import datetime
import io


def sign_digital_signature(user, certificate, password, reason):
    ds = models.DigitalSignature.objects(user=user).order_by("-id").first()
    p12 = pkcs12.load_key_and_certificates(
        ds.file.read(), passwod.encode(), backends.default_backend()
    )

    if not reason.strip():
        reason = "Issued Certification by Department of Computer Engineering"

    endorser = certificate.class_.get_endorser(user)
    if not endorser:
        return None

    now = datetime.datetime.now()
    date_str = now.strftime("D:%Y%m%d%H%M%S+00'00'")
    box = [0, 0, 100, 8]
    order = int(endorser.endorser_id[-1:])
    box[0] = box[0] + (box[2] * (order - 1))
    box[2] = box[2] * order
    dct = {
        "aligned": 0,
        "sigflags": 3,
        "sigflagsft": 132,
        "sigpage": 0,
        "sigbutton": True,
        "sigfield": endorser.endorser_id,
        "auto_sigfield": True,
        "sigandcertify": True,
        "signaturebox": box,
        "signature": f"{endorser.title} {endorser.first_name} {endorser.last_name}".strip(),
        "text": {"textalign": "center", "fontsize": 5},
        "contact": user.email,
        "location": "Hat Yai, Thailand",
        "signingdate": date_str,
        "reason": reason,
    }

    signed_file = sign_cms(certificate.file, p12, endorser)
    certificate.file.replace(signed_file)
    certificate.save()


def sign_cms(document_fp, p12, dct):
    datau = document_fp.read()
    datas = cms.sign(datau, dct, p12[0], p12[1], p12[2], "sha256")
    fileio = io.BytesIO()
    fileio.write(datau)
    fileio.write(datas)
    fileio.seek(0)

    return fileio
