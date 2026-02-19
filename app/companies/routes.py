from __future__ import annotations

import json

from flask import request
from flask_login import current_user, login_required

from ..api_utils import api_error, api_ok, ensure_company_scope, log_action
from ..extensions import db
from ..models import Company, UserAccount
from . import bp

def _normalize_organization_structure(data: dict):
    if 'organization_structure_lines' in data and 'organization_structure' not in data:
        rows = []
        for raw_line in (data.get('organization_structure_lines') or '').splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if '|' in line:
                name, description = [part.strip() for part in line.split('|', 1)]
            else:
                name, description = line, ''
            if name:
                rows.append({'name': name, 'description': description})
        data['organization_structure'] = json.dumps(rows, ensure_ascii=False)

    if 'organization_structure' in data and isinstance(data.get('organization_structure'), list):
        data['organization_structure'] = json.dumps(data['organization_structure'], ensure_ascii=False)


@bp.post('')
@login_required
def create_company():
    data = request.get_json() or {}
    if 'name' not in data:
        return api_error('invalid_payload')

    _normalize_organization_structure(data)

    company = Company(
        name=data['name'],
        business_model=data.get('business_model'),
        description=data.get('description'),
        accounting_method=data.get('accounting_method'),
        capital=data.get('capital'),
        tax_info=data.get('tax_info'),
        organization_structure=data.get('organization_structure'),
        goals=data.get('goals'),
        created_by=current_user.id,
    )
    db.session.add(company)
    db.session.flush()

    current_user.company_id = company.id
    log_action('company.create', 'company', str(company.id), company.id, {'name': company.name})
    db.session.commit()
    return api_ok({'id': company.id, 'name': company.name}, status=201)


@bp.get('')
@login_required
def list_companies():
    if current_user.company_id:
        companies = Company.query.filter_by(id=current_user.company_id).all()
    else:
        companies = Company.query.order_by(Company.id.desc()).all()
    return api_ok([
        {
            'id': c.id,
            'name': c.name,
            'business_model': c.business_model,
            'description': c.description,
            'accounting_method': c.accounting_method,
            'capital': c.capital,
        }
        for c in companies
    ])


@bp.get('/<int:company_id>')
@login_required
def get_company(company_id: int):
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)
    c = Company.query.get_or_404(company_id)
    return api_ok(
        {
            'id': c.id,
            'name': c.name,
            'business_model': c.business_model,
            'description': c.description,
            'accounting_method': c.accounting_method,
            'capital': c.capital,
            'tax_info': c.tax_info,
            'organization_structure': c.organization_structure,
            'organization_structure_items': json.loads(c.organization_structure) if c.organization_structure else [],
            'goals': c.goals,
        }
    )


@bp.put('/<int:company_id>')
@login_required
def update_company(company_id: int):
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)
    data = request.get_json() or {}
    _normalize_organization_structure(data)
    company = Company.query.get_or_404(company_id)

    for field in [
        'name',
        'business_model',
        'description',
        'accounting_method',
        'capital',
        'tax_info',
        'organization_structure',
        'goals',
    ]:
        if field in data:
            setattr(company, field, data.get(field))

    log_action('company.update', 'company', str(company.id), company.id, {'name': company.name})
    db.session.commit()
    return api_ok({'id': company.id, 'name': company.name})
