import datetime


import io
import cairosvg
import qrcode
import base64
import copy

import PIL

from lxml import etree

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, PackageLoader, select_autoescape, Template

import mongoengine as me
from viyyoor import models

import logging

logger = logging.getLogger(__name__)


class PSUSMTP:
    def __init__(self, setting):
        self.setting = setting
        self.host = setting.get("VIYYOOR_EMAIL_HOST")
        self.port = setting.get("VIYYOOR_EMAIL_PORT")
        self.user = setting.get("VIYYOOR_EMAIL_USER")
        self.password = setting.get("VIYYOOR_EMAIL_PASSWORD")
        self.server = smtplib.SMTP(self.host, self.port)

    def login(self):
        try:
            self.server.starttls()
            self.server.login(self.user, self.password)
        except Exception as e:
            logger.exception(e)
            return False
        return True

    def quit(self):
        self.server.quit()

    def send_email(self, certificate, receiver, subject, body):
        try:
            sender = self.setting.get("VIYYOOR_EMAIL_USER")
            receivers = [receiver]

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender
            message["To"] = receiver

            email_body = MIMEText(body, "plain")
            message.attach(email_body)

            self.server.sendmail(sender, receivers, message.as_string())

            certificate.emails[-1].status = "sent"
            certificate.save()

        except Exception as e:
            logger.exception(e)
            certificate.emails[-1].status = "failed"
            certificate.save()
            return False

        return True


def get_text_format(class_, participant, certificate):
    if not class_ or not participant or not certificate:
        return

    text_format = {
        "class_name": class_.name,
        "class_printed_name": class_.printed_name,
        "class_description": class_.description,
        "class_started_date": class_.started_date,
        "class_ended_date": class_.ended_date,
        "class_issued_date": class_.issued_date,
        "participant_name": participant.name,
        "participant_group": participant.group,
        "participant_commond_id": participant.common_id,
        "participant_organization": participant.organization,
        "certificate_url": certificate.validated_url,
        "certificate_class_date": class_.class_date_text,
    }

    return text_format


def send_email_participant_in_class(
    class_,
    setting,
):
    email_template = class_.organization.get_email_template()
    if not email_template:
        logger.debug(f"there are no email template for {class_.organization.name}")

    psu_smtp = PSUSMTP(setting)
    if not email_template:
        logger.debug("email template not found")
        return False

    if not psu_smtp.login():
        logger.debug("PSUSMTP login failed...")
        return False

    psu_smtp = PSUSMTP(setting)
    if not psu_smtp.login():
        logger.debug(f"email cannot login")
        return False

    logger.debug(f"send email in class { class_.name }")

    certificates = models.Certificate.objects(
        me.Q(**{"emails__status": "waiting", "class_": class_})
    )
    for certificate in certificates:
        participant = certificate.get_participant()

        template_subject = Template(email_template.subject)
        template_body = Template(email_template.body)

        text_format = get_text_format(class_, participant, certificate)
        email_subject = template_subject.render(text_format)
        email_body = template_body.render(text_format)

        logger.debug(f"send email to {participant.email}")
        psu_smtp.send_email(certificate, participant.email, email_subject, email_body)

    psu_smtp.quit()
    return True


def force_send_email_certificate(
    certificate,
    setting,
):
    participant = certificate.get_participant()
    class_ = certificate.class_
    organization = class_.organization

    email_template = organization.get_email_template()

    if not email_template:
        logger.debug(f"There are no email template for {class_.organization.name}")
        return False

    if not participant.email:
        logger.debug(f"attendant {participant.name} email is required")
        return False

    psu_smtp = PSUSMTP(setting)
    if not psu_smtp.login():
        logger.debug(f"email cannot login")
        return False

    template_subject = Template(email_template.subject)
    template_body = Template(email_template.body)

    text_format = get_text_format(class_, participant, certificate)

    email_subject = template_subject.render(text_format)
    email_body = template_body.render(text_format)

    logger.debug(f"send email to {participant.email}")
    if psu_smtp.send_email(certificate, participant.email, email_subject, email_body):
        psu_smtp.quit()
        return True

    psu_smtp.quit()
    return False
