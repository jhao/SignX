from __future__ import annotations

from functools import wraps
from typing import Iterable

from flask import abort
from flask_login import current_user


class Role:
    ADMIN = 'admin'
    SENDER = 'sender'
    SIGNER = 'signer'


ROLE_HIERARCHY = {
    Role.ADMIN: {Role.SENDER, Role.SIGNER, Role.ADMIN},
    Role.SENDER: {Role.SENDER},
    Role.SIGNER: {Role.SIGNER},
}


def _has_roles(user_roles: Iterable[str], required: Iterable[str]) -> bool:
    expanded = set()
    for role in user_roles:
        expanded.update(ROLE_HIERARCHY.get(role, {role}))
    return set(required).issubset(expanded)


def require_roles(*roles: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not _has_roles(current_user.roles, roles):
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator
