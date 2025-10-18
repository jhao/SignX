from __future__ import annotations

import secrets
from datetime import datetime

from flask import jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from ..emailer import EmailRequest, send_mail
from ..extensions import db
from ..models import Notification, User, roles_users
from ..rbac import Role
from . import bp


@bp.post('/register')
def register():
    data = request.get_json() or {}
    if not {'email', 'password', 'name'} <= data.keys():
        return jsonify({'error': 'invalid_payload'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'email_exists'}), 409
    user = User(email=data['email'], name=data['name'], password_hash=generate_password_hash(data['password']))
    db.session.add(user)
    db.session.commit()
    db.session.execute(
        roles_users.insert().values(user_id=user.id, role=Role.SENDER)
    )
    db.session.commit()
    notification = send_mail(
        EmailRequest(
            recipients=[user.email],
            subject='Welcome to SignX',
            body='Your account has been created successfully.',
        )
    )
    notification.user = user
    db.session.add(notification)
    db.session.commit()
    return jsonify({'id': user.id, 'email': user.email, 'name': user.name})


@bp.post('/login')
def login():
    data = request.get_json() or {}
    if not {'email', 'password'} <= data.keys():
        return jsonify({'error': 'invalid_payload'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'invalid_credentials'}), 401
    login_user(user, remember=data.get('remember', False))
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'id': user.id, 'email': user.email, 'name': user.name})


@bp.post('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'status': 'logged_out'})


@bp.post('/reset-request')
def reset_request():
    data = request.get_json() or {}
    if 'email' not in data:
        return jsonify({'error': 'invalid_payload'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'status': 'ok'})
    token = secrets.token_urlsafe(32)
    notification = send_mail(
        EmailRequest(
            recipients=[user.email],
            subject='Reset your SignX password',
            body=f'Use this token to reset your password: {token}',
        )
    )
    notification.user = user
    db.session.add(notification)
    db.session.commit()
    return jsonify({'status': 'ok', 'token': token})


@bp.post('/reset')
def reset_password():
    data = request.get_json() or {}
    if not {'email', 'password'} <= data.keys():
        return jsonify({'error': 'invalid_payload'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': 'not_found'}), 404
    user.password_hash = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify({'status': 'ok'})


@bp.get('/me')
@login_required
def me():
    return jsonify({'id': current_user.id, 'email': current_user.email, 'name': current_user.name})
