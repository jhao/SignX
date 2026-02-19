from __future__ import annotations

from flask import request
from flask_login import login_required

from ..ai_service import (
    AI_MODEL_SETTING_KEY,
    get_model_preset,
    get_ai_model_settings,
    get_model_presets,
    save_ai_model_settings,
)
from ..api_utils import api_error, api_ok, require_platform_roles
from ..extensions import db
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


@bp.get('/settings/ai-model')
@login_required
@require_platform_roles(PlatformRole.PLATFORM_ADMIN)
def get_ai_model_setting():
    settings = get_ai_model_settings()
    sanitized = dict(settings)
    if sanitized.get('api_key'):
        sanitized['api_key'] = '***'
    return api_ok({'current': sanitized, 'presets': get_model_presets()})


@bp.put('/settings/ai-model')
@login_required
@require_platform_roles(PlatformRole.PLATFORM_ADMIN)
def update_ai_model_setting():
    data = request.get_json() or {}
    preset = get_model_preset(data.get('preset_id'))
    if not preset:
        return api_error('invalid_payload')

    current = get_ai_model_settings()
    incoming_key = data.get('api_key')
    api_key = current.get('api_key') if incoming_key in (None, '', '***') else incoming_key
    if not api_key:
        return api_error('invalid_payload')

    setting = save_ai_model_settings(
        {
            'preset_id': preset['id'],
            'provider': preset['provider'],
            'model_type': preset['model_type'],
            'base_url': preset['base_url'],
            'model': preset['model'],
            'api_key': api_key,
        }
    )
    db.session.merge(setting)
    db.session.commit()
    return api_ok({'key': AI_MODEL_SETTING_KEY})
