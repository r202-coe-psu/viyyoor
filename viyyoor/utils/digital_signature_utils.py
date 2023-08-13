from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms
from psusigner import PSUSigner

import datetime
import io

from viyyoor import models

import logging

logger = logging.getLogger(__name__)


from . import email_utils


def sign_certificates(class_id, settings):
    issuer_printed_name = settings.get("ISSUER_PRINTED_NAME")
    issuer_contact_email = settings.get("ISSUER_CONTACT_EMAIL")

    class_ = models.Class.objects.get(id=class_id)
    certificates = models.Certificate.objects(class_=class_, status="signing")
    organization = class_.organization
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

    if not class_.is_quota_enough_to_prepair():
        print("Quota is Out")
        raise Exception("Quota is Out")

    """
    quota = models.CertificateQuota.objects(
        organization=organization, available_number__gt=0, status="active"
    ).first()
    if not quota:
        logger.debug("Quota is Out")
        raise Exception("Quota is Out")

    quota_usage = models.CertificateQuotaUsage(
        organization=organization, class_=class_, certificate_quota=quota
    )
    """

    for certificate in certificates:
        participant = certificate.get_participant()
        sign_digital_signature(
            certificate, dc, issuer_printed_name, issuer_contact_email
        )
        certificate.signed_date = datetime.datetime.now()
        certificate.status = "completed"
        certificate.privacy = "public"
        """
        if not certificate.is_sent_email_participant() and participant.email:
            certificate.emails.create(
                receiver_email=participant.email,
                status="waiting",
                sent_date=datetime.datetime.now(),
                remark="auto send",
            )
        """
        certificate.updated_date = datetime.datetime.now()
        certificate.save()

        """
        q_usage = models.CertificateQuotaUsage.objects(certificates=certificate).first()
        if q_usage:
            continue

        quota.available_number -= 1
        quota.save()

        quota_usage.certificates.append(certificate)
        quota_usage.number += 1
        quota_usage.updated_date = datetime.datetime.now()
        quota_usage.save()

        if quota.available_number <= 0:
            quota = models.CertificateQuota.objects(
                organization=organization, available_number__gt=0, status="active"
            ).first()
            quota_usage = models.CertificateQuotaUsage(
                organization=organization, class_=class_, certificate_quota=quota
            )
            if not quota:
                logging.debug("Quota is Out")
                raise Exception("Quota is Out")
        """

    # Send email to participant in every 'completed' certificates
    # logging.debug("singed completed, sending email")
    # email_utils.send_email_participant_in_class(class_, settings)


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
        "sigflags": 1,
        "sigflagsft": 132,
        "sigpage": 0,
        "sigbutton": True,
        "auto_sigfield": True,
        "sigandcertify": True,
        "sigfield": "Signature",
        "signaturebox": box,
        "signature": issuer_printed_name,
        # "text": {"textalign": "center", "fontsize": 5},
        "text": {"textalign": "left", "fontsize": 5},
        "contact": issuer_contact_email,
        "location": "Hat Yai, Thailand",
        "signingdate": date_str,
        "reason": reason,
    }

    if dc.type_ == "self":
        sign_by_self(dct, dc, certificate)
    elif dc.type_ == "psusigner":
        sign_by_psusigner(
            dct,
            dc,
            certificate,
            ref1=str(certificate.id),
            ref2=certificate.class_.printed_name,
            remark=reason,
        )

    certificate.save()


def sign_by_psusigner(dct, dc, certificate, **kwargs):
    signer = PSUSigner(
        code=dc.signer_api.code,
        secret=dc.decrypt_password(dc.signer_api.secret).decode(),
        agent_key=dc.decrypt_password(dc.signer_api.agent_key).decode(),
        jwt_secret=dc.decrypt_password(dc.signer_api.jwt_secret).decode(),
        api_url=dc.signer_api.api_url,
    )

    signed_byte = signer.sign_byte(certificate.file.read(), dct, **kwargs)
    certificate.file.replace(signed_byte)


def sign_by_self(dct, dc, certificate):
    password = dc.decrypt_password(dc.password)
    dc.file.seek(0)
    p12 = pkcs12.load_key_and_certificates(
        dc.file.read(), password, backends.default_backend()
    )

    signed_file = sign_cms(certificate.file, p12, dct)
    certificate.file.replace(signed_file)
    certificate.ca_download_url = dc.ca_download_url


def sign_cms(document_fp, p12, dct):
    datau = document_fp.read()
    datas = cms.sign(datau, dct, p12[0], p12[1], p12[2], "sha256")
    fileio = io.BytesIO()
    fileio.write(datau)
    fileio.write(datas)
    fileio.seek(0)

    return fileio
