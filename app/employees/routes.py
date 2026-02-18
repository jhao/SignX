from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from ..api_utils import api_error, api_ok, ensure_company_scope, log_action
from ..extensions import db
from ..models import CompanyRole, Employee
from . import bp


@bp.post('')
@login_required
def create_employee():
    data = request.get_json() or {}
    required = {'company_id', 'name'}
    if not required.issubset(data):
        return api_error('invalid_payload')
    company_id = int(data['company_id'])
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    employee = Employee(
        company_id=company_id,
        name=data['name'],
        primary_tasks=data.get('primary_tasks'),
        role_id=data.get('role_id'),
        company_role=CompanyRole(data.get('company_role', CompanyRole.MEMBER.value)),
        ai_provider=data.get('ai_provider'),
        api_key_encrypted=data.get('api_key_encrypted'),
        photo_path=data.get('photo_path'),
        created_by=current_user.id,
    )
    db.session.add(employee)
    log_action('employee.create', 'employee', None, company_id, {'name': employee.name})
    db.session.commit()
    return api_ok({'id': employee.id, 'name': employee.name}, status=201)


@bp.get('')
@login_required
def list_employees():
    company_id = request.args.get('company_id', type=int) or current_user.company_id
    if not company_id:
        return api_error('company_id_required')
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    employees = Employee.query.filter_by(company_id=company_id).order_by(Employee.id.desc()).all()
    return api_ok([
        {
            'id': e.id,
            'name': e.name,
            'company_role': e.company_role.value,
            'primary_tasks': e.primary_tasks,
            'ai_provider': e.ai_provider,
            'api_key_masked': '***' if e.api_key_encrypted else None,
        }
        for e in employees
    ])
