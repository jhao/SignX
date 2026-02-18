from __future__ import annotations

from datetime import datetime
from functools import wraps

from flask import jsonify, request
from flask_login import current_user

from .extensions import db
from .models import AuditLog, PlatformRole


def api_ok(data=None, message='ok', code=0, status=200):
    return jsonify({'code': code, 'message': message, 'data': data}), status


def api_error(message='error', code=1, status=400):
    return jsonify({'code': code, 'message': message, 'data': None}), status


def require_platform_roles(*roles: PlatformRole):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return api_error('unauthorized', status=401)
            if roles and current_user.platform_role not in roles:
                return api_error('forbidden', status=403)
            return func(*args, **kwargs)

        return wrapped

    return decorator


def ensure_company_scope(company_id: int):
    if current_user.platform_role == PlatformRole.PLATFORM_ADMIN:
        return True
    return current_user.company_id == company_id


def parse_iso_datetime(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value)


def log_action(action: str, resource_type: str, resource_id: str | None = None, company_id: int | None = None, details: dict | None = None):
    db.session.add(
        AuditLog(
            company_id=company_id,
            actor_user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=request.remote_addr,
        )
    )
