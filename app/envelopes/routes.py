from __future__ import annotations

import secrets

from flask import jsonify, render_template, request, url_for
from flask_login import current_user, login_required

from ..emailer import EmailRequest, send_mail
from ..extensions import db
from ..models import Document, Envelope, EnvelopeStatus, Notification, Signer
from ..rbac import Role, require_roles
from ..storage import save_upload
from . import bp


@bp.get('/')
@login_required
@require_roles(Role.SENDER, Role.ADMIN)
def list_envelopes():
    envelopes = Envelope.query.filter_by(creator_id=current_user.id).all()
    return jsonify([
        {
            'id': e.id,
            'subject': e.subject,
            'status': e.status.value,
            'created_at': e.created_at.isoformat(),
        }
        for e in envelopes
    ])


@bp.post('/')
@login_required
@require_roles(Role.SENDER, Role.ADMIN)
def create_envelope():
    data = request.form or request.get_json() or {}
    if 'subject' not in data:
        return jsonify({'error': 'invalid_payload'}), 400
    envelope = Envelope(subject=data['subject'], message=data.get('message'), creator=current_user)
    envelope.ensure_expiration()
    db.session.add(envelope)

    files = request.files.getlist('files') if request.files else []
    for file in files:
        path = save_upload(file, file.filename)
        document = Document(envelope=envelope, filename=file.filename, original_path=str(path))
        db.session.add(document)

    signers_data = data.get('signers', []) if isinstance(data.get('signers'), list) else []
    for index, signer_data in enumerate(signers_data, start=1):
        signer = Signer(
            envelope=envelope,
            name=signer_data['name'],
            email=signer_data['email'],
            order=index,
            invite_token=secrets.token_urlsafe(32),
        )
        db.session.add(signer)

    db.session.commit()
    return jsonify({'id': envelope.id, 'status': envelope.status.value})


@bp.post('/<int:envelope_id>/send')
@login_required
@require_roles(Role.SENDER, Role.ADMIN)
def send_envelope(envelope_id: int):
    envelope = Envelope.query.get_or_404(envelope_id)
    if envelope.creator != current_user:
        return jsonify({'error': 'forbidden'}), 403
    try:
        envelope.set_status(EnvelopeStatus.SENT)
    except ValueError:
        return jsonify({'error': 'invalid_status'}), 400
    notifications: list[Notification] = []
    for signer in envelope.signers:
        link = url_for('signing.validate_link', token=signer.invite_token, _external=True)
        notification = send_mail(
            EmailRequest(
                recipients=[signer.email],
                subject=f'Signature request for {envelope.subject}',
                body=f'Please sign the document: {link}',
            )
        )
        notification.signer = signer
        notification.envelope = envelope
        notifications.append(notification)
    db.session.add_all(notifications)
    db.session.commit()
    return jsonify({'status': envelope.status.value})


@bp.get('/<int:envelope_id>')
@login_required
def detail(envelope_id: int):
    envelope = Envelope.query.get_or_404(envelope_id)
    if envelope.creator != current_user and not any(s.email == current_user.email for s in envelope.signers):
        return jsonify({'error': 'forbidden'}), 403
    return jsonify(
        {
            'id': envelope.id,
            'subject': envelope.subject,
            'message': envelope.message,
            'status': envelope.status.value,
            'documents': [
                {
                    'id': d.id,
                    'filename': d.filename,
                    'pdf_path': d.pdf_path,
                }
                for d in envelope.documents
            ],
            'signers': [
                {
                    'id': s.id,
                    'name': s.name,
                    'email': s.email,
                    'has_signed': s.has_signed,
                }
                for s in envelope.signers
            ],
        }
    )


@bp.get('/wizard')
@login_required
@require_roles(Role.SENDER, Role.ADMIN)
def create_wizard():
    envelopes = Envelope.query.filter_by(creator_id=current_user.id).all()
    return render_template('dashboard.html', envelopes=envelopes)
