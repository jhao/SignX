from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from ..ai_service import generate_employee_agent_prompt
from ..api_utils import api_error, api_ok, ensure_company_scope, log_action
from ..extensions import db
from ..models import CompanyRole, Employee
from . import bp


def _apply_employee_payload(employee: Employee, data: dict):
    if 'name' in data:
        employee.name = data['name']
    if 'primary_tasks' in data:
        employee.primary_tasks = data.get('primary_tasks')
    if 'role_id' in data:
        employee.role_id = data.get('role_id')
    if 'company_role' in data and data.get('company_role'):
        employee.company_role = CompanyRole(data.get('company_role'))
    if 'ai_provider' in data:
        employee.ai_provider = data.get('ai_provider')
    if 'api_key_encrypted' in data:
        employee.api_key_encrypted = data.get('api_key_encrypted')
    if 'photo_path' in data:
        employee.photo_path = data.get('photo_path')


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

    if data.get('generate_agent_prompt'):
        try:
            employee.agent_prompt = generate_employee_agent_prompt(
                name=employee.name,
                primary_tasks=employee.primary_tasks,
                company_role=employee.company_role.value,
            )
        except ValueError as exc:
            if str(exc) == 'ai_model_not_configured':
                return api_error('ai_model_not_configured')
            raise
        except Exception:
            return api_error('ai_prompt_generation_failed', status=502)

    db.session.add(employee)
    log_action('employee.create', 'employee', None, company_id, {'name': employee.name})
    db.session.commit()
    return api_ok({'id': employee.id, 'name': employee.name, 'agent_prompt': employee.agent_prompt}, status=201)


@bp.put('/<int:employee_id>')
@login_required
def update_employee(employee_id: int):
    employee = Employee.query.get_or_404(employee_id)
    if not ensure_company_scope(employee.company_id):
        return api_error('forbidden', status=403)

    data = request.get_json() or {}
    _apply_employee_payload(employee, data)

    if data.get('generate_agent_prompt'):
        try:
            employee.agent_prompt = generate_employee_agent_prompt(
                name=employee.name,
                primary_tasks=employee.primary_tasks,
                company_role=employee.company_role.value,
            )
        except ValueError as exc:
            if str(exc) == 'ai_model_not_configured':
                return api_error('ai_model_not_configured')
            raise
        except Exception:
            return api_error('ai_prompt_generation_failed', status=502)

    if 'agent_prompt' in data:
        employee.agent_prompt = data.get('agent_prompt')

    log_action('employee.update', 'employee', str(employee.id), employee.company_id, {'name': employee.name})
    db.session.commit()
    return api_ok({'id': employee.id, 'name': employee.name, 'agent_prompt': employee.agent_prompt})


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
            'agent_prompt': e.agent_prompt,
            'api_key_masked': '***' if e.api_key_encrypted else None,
        }
        for e in employees
    ])
