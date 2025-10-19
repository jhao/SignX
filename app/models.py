from __future__ import annotations

import enum
from datetime import datetime, timedelta
from typing import List

from flask_login import UserMixin
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db, login_manager


class EnvelopeStatus(enum.StrEnum):
    DRAFT = 'draft'
    SENT = 'sent'
    VIEWED = 'viewed'
    SIGNED = 'signed'
    COMPLETED = 'completed'
    VOIDED = 'voided'

    @classmethod
    def transition(cls, current: 'EnvelopeStatus', target: 'EnvelopeStatus') -> bool:
        allowed = {
            cls.DRAFT: {cls.SENT, cls.VOIDED},
            cls.SENT: {cls.VIEWED, cls.SIGNED, cls.VOIDED},
            cls.VIEWED: {cls.SIGNED, cls.VOIDED},
            cls.SIGNED: {cls.COMPLETED, cls.VOIDED},
            cls.COMPLETED: set(),
            cls.VOIDED: set(),
        }
        return target in allowed.get(current, set())


roles_users = db.Table(
    'roles_users',
    Column('user_id', ForeignKey('user.id'), primary_key=True),
    Column('role', String(32), primary_key=True),
)


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    envelopes: Mapped[List['Envelope']] = relationship(back_populates='creator')
    notifications: Mapped[List['Notification']] = relationship(back_populates='user')

    def __repr__(self) -> str:  # pragma: no cover - repr only
        return f'<User {self.email}>'

    @property
    def roles(self) -> List[str]:
        result = db.session.execute(
            roles_users.select().where(roles_users.c.user_id == self.id)
        )
        return [row.role for row in result]


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


class Envelope(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[EnvelopeStatus] = mapped_column(Enum(EnvelopeStatus), default=EnvelopeStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    creator_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)

    creator: Mapped[User] = relationship(back_populates='envelopes')
    documents: Mapped[List['Document']] = relationship(back_populates='envelope', cascade='all, delete-orphan')
    signers: Mapped[List['Signer']] = relationship(back_populates='envelope', cascade='all, delete-orphan')
    audit_events: Mapped[List['AuditEvent']] = relationship(back_populates='envelope', cascade='all, delete-orphan')

    def set_status(self, target: EnvelopeStatus) -> None:
        if self.status == target:
            return
        previous = self.status
        if not EnvelopeStatus.transition(previous, target):
            raise ValueError(f'Invalid transition {self.status} -> {target}')
        self.status = target
        db.session.add(
            AuditEvent(
                envelope=self,
                event_type='status_change',
                payload={'from': previous.value, 'to': target.value},
            )
        )

    def ensure_expiration(self, ttl_hours: int = 72) -> None:
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)


class Document(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    envelope_id: Mapped[int] = mapped_column(ForeignKey('envelope.id'), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str] = mapped_column(String(512), nullable=False)
    pdf_path: Mapped[str] = mapped_column(String(512))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    envelope: Mapped[Envelope] = relationship(back_populates='documents')
    fields: Mapped[List['Field']] = relationship(back_populates='document', cascade='all, delete-orphan')
    signatures: Mapped[List['Signature']] = relationship(back_populates='document', cascade='all, delete-orphan')


class Signer(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    envelope_id: Mapped[int] = mapped_column(ForeignKey('envelope.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    access_code: Mapped[str | None] = mapped_column(String(64))
    invite_token: Mapped[str | None] = mapped_column(String(128), unique=True)
    has_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=1)

    envelope: Mapped[Envelope] = relationship(back_populates='signers')
    signatures: Mapped[List['Signature']] = relationship(back_populates='signer', cascade='all, delete-orphan')
    notifications: Mapped[List['Notification']] = relationship(back_populates='signer')


class Field(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('document.id'), nullable=False)
    signer_id: Mapped[int] = mapped_column(ForeignKey('signer.id'), nullable=False)
    field_type: Mapped[str] = mapped_column(String(32), nullable=False)
    page: Mapped[int] = mapped_column(Integer, default=1)
    x: Mapped[float] = mapped_column(db.Float, nullable=False)
    y: Mapped[float] = mapped_column(db.Float, nullable=False)
    width: Mapped[float] = mapped_column(db.Float, nullable=False)
    height: Mapped[float] = mapped_column(db.Float, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    document: Mapped[Document] = relationship(back_populates='fields')
    signer: Mapped[Signer] = relationship()


class Signature(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('document.id'), nullable=False)
    signer_id: Mapped[int] = mapped_column(ForeignKey('signer.id'), nullable=False)
    field_id: Mapped[int | None] = mapped_column(ForeignKey('field.id'))
    image_data: Mapped[bytes | None] = mapped_column(LargeBinary)
    stamp_path: Mapped[str | None] = mapped_column(String(512))
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped[Document] = relationship(back_populates='signatures')
    signer: Mapped[Signer] = relationship(back_populates='signatures')
    field: Mapped[Field | None] = relationship()
    crypto_record: Mapped['CryptoRecord'] = relationship(back_populates='signature', uselist=False)


class CryptoRecord(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signature_id: Mapped[int] = mapped_column(ForeignKey('signature.id'), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    certificate_subject: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    signature_bytes: Mapped[bytes] = mapped_column(LargeBinary)

    signature: Mapped[Signature] = relationship(back_populates='crypto_record')


class AuditEvent(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    envelope_id: Mapped[int] = mapped_column(ForeignKey('envelope.id'), nullable=False)
    signer_id: Mapped[int | None] = mapped_column(ForeignKey('signer.id'))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(db.JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    envelope: Mapped[Envelope] = relationship(back_populates='audit_events')
    signer: Mapped[Signer | None] = relationship()


class Notification(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('user.id'))
    signer_id: Mapped[int | None] = mapped_column(ForeignKey('signer.id'))
    envelope_id: Mapped[int | None] = mapped_column(ForeignKey('envelope.id'))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    success: Mapped[bool | None] = mapped_column(Boolean)

    user: Mapped[User | None] = relationship(back_populates='notifications')
    signer: Mapped[Signer | None] = relationship(back_populates='notifications')
    envelope: Mapped[Envelope | None] = relationship()
