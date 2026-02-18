from __future__ import annotations

from datetime import datetime

from flask import request
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from ..api_utils import api_error, api_ok
from ..extensions import db
from ..models import PlatformRole, UserAccount
from . import bp


@bp.post('/register')
def register():
    data = request.get_json() or {}
    required = {'email', 'password', 'full_name'}
    if not required.issubset(data):
        return api_error('invalid_payload')

    if UserAccount.query.filter_by(email=data['email']).first():
        return api_error('email_exists', status=409)

    account = UserAccount(
        email=data['email'],
        full_name=data['full_name'],
        password_hash=generate_password_hash(data['password']),
        platform_role=PlatformRole(data.get('platform_role', PlatformRole.USER.value)),
        company_id=data.get('company_id'),
    )
    db.session.add(account)
    db.session.commit()
    return api_ok({'id': account.id, 'email': account.email, 'platform_role': account.platform_role.value}, status=201)


@bp.post('/login')
def login():
    data = request.get_json() or {}
    if not {'email', 'password'}.issubset(data):
        return api_error('invalid_payload')

    user = UserAccount.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return api_error('invalid_credentials', status=401)

    login_user(user, remember=bool(data.get('remember')))
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    return api_ok({'id': user.id, 'email': user.email, 'company_id': user.company_id, 'platform_role': user.platform_role.value})


@bp.post('/logout')
@login_required
def logout():
    logout_user()
    return api_ok({'status': 'logged_out'})


@bp.get('/me')
@login_required
def me():
    return api_ok(
        {
            'id': current_user.id,
            'email': current_user.email,
            'full_name': current_user.full_name,
            'company_id': current_user.company_id,
            'platform_role': current_user.platform_role.value,
            'last_login_at': current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        }
    )
