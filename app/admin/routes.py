from __future__ import annotations

from flask import request
from flask_login import login_required

from ..api_utils import api_error, api_ok, require_platform_roles
from ..models import AuditLog, Company, PlatformRole, UserAccount
from . import bp


@bp.get('/tenants')
@login_required
@require_platform_roles(PlatformRole.PLATFORM_ADMIN)
def list_tenants():
    tenants = Company.query.order_by(Company.created_at.desc()).all()
    return api_ok([
        {
            'id': tenant.id,
            'name': tenant.name,
            'business_model': tenant.business_model,
            'created_at': tenant.created_at.isoformat(),
        }
        for tenant in tenants
    ])


@bp.get('/users')
@login_required
@require_platform_roles(PlatformRole.PLATFORM_ADMIN)
def list_users():
    users = UserAccount.query.order_by(UserAccount.id.desc()).all()
    return api_ok([
        {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'platform_role': user.platform_role.value,
            'company_id': user.company_id,
        }
        for user in users
    ])


@bp.get('/audits')
@login_required
@require_platform_roles(PlatformRole.PLATFORM_ADMIN)
def list_audits():
    company_id = request.args.get('company_id', type=int)
    query = AuditLog.query
    if company_id:
        query = query.filter_by(company_id=company_id)
    logs = query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return api_ok([
        {
            'id': log.id,
            'company_id': log.company_id,
            'actor_user_id': log.actor_user_id,
            'action': log.action,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'details': log.details,
            'created_at': log.created_at.isoformat(),
        }
        for log in logs
    ])
