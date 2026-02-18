from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from ..api_utils import api_error, api_ok, ensure_company_scope, log_action
from ..extensions import db
from ..models import Company, UserAccount
from . import bp


@bp.post('')
@login_required
def create_company():
    data = request.get_json() or {}
    if 'name' not in data:
        return api_error('invalid_payload')

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
            'goals': c.goals,
        }
    )
