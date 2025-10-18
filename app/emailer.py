from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from flask import current_app
from flask_mail import Message

from .extensions import mail
from .models import Notification


@dataclass
class EmailRequest:
    recipients: list[str]
    subject: str
    body: str
    html: str | None = None


def send_mail(request: EmailRequest) -> Notification:
    message = Message(subject=request.subject, recipients=request.recipients, body=request.body, html=request.html)
    notification = Notification(subject=request.subject, body=request.body)
    notification.sent_at = datetime.utcnow()
    try:
        mail.send(message)
        notification.success = True
    except Exception as exc:  # pragma: no cover - external dependency
        current_app.logger.exception('Mail sending failed: %s', exc)
        notification.success = False
    return notification


def send_bulk(requests: Iterable[EmailRequest]) -> list[Notification]:
    return [send_mail(req) for req in requests]
