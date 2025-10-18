from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required

from ..extensions import db
from ..models import AuditEvent, Envelope, EnvelopeStatus, Notification, User
from ..rbac import Role, require_roles
from . import bp


@bp.get('/users')
@login_required
@require_roles(Role.ADMIN)
def list_users():
    users = User.query.all()
    return jsonify([
        {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'roles': user.roles,
        }
        for user in users
    ])


@bp.get('/audits')
@login_required
@require_roles(Role.ADMIN)
def audit_events():
    envelope_id = request.args.get('envelope_id', type=int)
    query = AuditEvent.query
    if envelope_id:
        query = query.filter_by(envelope_id=envelope_id)
    events = query.order_by(AuditEvent.occurred_at.desc()).limit(100).all()
    return jsonify([
        {
            'id': event.id,
            'envelope_id': event.envelope_id,
            'event_type': event.event_type,
            'payload': event.payload,
            'occurred_at': event.occurred_at.isoformat(),
        }
        for event in events
    ])


@bp.get('/notifications')
@login_required
@require_roles(Role.ADMIN)
def list_notifications():
    notifications = Notification.query.order_by(Notification.sent_at.desc().nullslast()).limit(100).all()
    return jsonify([
        {
            'id': notification.id,
            'subject': notification.subject,
            'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
            'success': notification.success,
        }
        for notification in notifications
    ])


@bp.post('/envelopes/<int:envelope_id>/void')
@login_required
@require_roles(Role.ADMIN)
def void_envelope(envelope_id: int):
    envelope = Envelope.query.get_or_404(envelope_id)
    envelope.set_status(EnvelopeStatus.VOIDED)
    db.session.commit()
    return jsonify({'status': envelope.status.value})
