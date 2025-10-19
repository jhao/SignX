from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from flask import current_app
from flask_apscheduler import APScheduler

from ..extensions import db, scheduler as app_scheduler
from ..models import Document, Envelope, EnvelopeStatus
from ..storage import convert_to_pdf, purge_expired_files


def register_jobs(scheduler: APScheduler) -> None:
    for job_id, func, trigger_args in [
        ('convert_pending_documents', convert_pending_documents, dict(trigger='interval', minutes=1)),
        ('expire_envelopes', expire_envelopes, dict(trigger='interval', minutes=10)),
        ('purge_storage', purge_storage, dict(trigger='cron', hour='3')),
    ]:
        if scheduler.get_job(job_id):
            continue
        scheduler.add_job(id=job_id, func=func, **trigger_args)


def convert_pending_documents():
    with app_scheduler.app.app_context():
        documents: Iterable[Document] = Document.query.filter(Document.pdf_path.is_(None)).all()
        for document in documents:
            try:
                pdf_path = convert_to_pdf(Path(document.original_path))
                document.pdf_path = str(pdf_path)
            except Exception as exc:  # pragma: no cover - background job logging
                current_app.logger.exception('Failed to convert %s: %s', document.filename, exc)
        db.session.commit()


def expire_envelopes():
    with app_scheduler.app.app_context():
        now = datetime.utcnow()
        envelopes: Iterable[Envelope] = Envelope.query.filter(
            Envelope.expires_at.is_not(None), Envelope.expires_at < now
        ).all()
        for envelope in envelopes:
            if envelope.status not in {EnvelopeStatus.COMPLETED, EnvelopeStatus.VOIDED}:
                envelope.set_status(EnvelopeStatus.VOIDED)
        db.session.commit()


def purge_storage():
    with app_scheduler.app.app_context():
        purge_expired_files(Path(current_app.config['STORAGE_DIR']))
