from __future__ import annotations

from flask import request
from flask_login import current_user, login_required
from sqlalchemy import func

from ..api_utils import api_error, api_ok, ensure_company_scope, log_action, parse_iso_datetime
from ..extensions import db
from ..models import FinancialRecord, FinancialRecordType, TokenUsage
from . import bp


@bp.post('/token-usage')
@login_required
def create_token_usage():
    data = request.get_json() or {}
    required = {'company_id', 'model', 'tokens_used', 'cost'}
    if not required.issubset(data):
        return api_error('invalid_payload')
    company_id = int(data['company_id'])
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    usage = TokenUsage(
        company_id=company_id,
        model=data['model'],
        tokens_used=int(data['tokens_used']),
        cost=float(data['cost']),
        usage_date=parse_iso_datetime(data.get('usage_date')),
        created_by=current_user.id,
    )
    db.session.add(usage)
    log_action('finance.token_usage.create', 'token_usage', None, company_id, {'model': usage.model})
    db.session.commit()
    return api_ok({'id': usage.id}, status=201)


@bp.post('/records')
@login_required
def create_financial_record():
    data = request.get_json() or {}
    required = {'company_id', 'description', 'amount', 'record_type'}
    if not required.issubset(data):
        return api_error('invalid_payload')
    company_id = int(data['company_id'])
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    record = FinancialRecord(
        company_id=company_id,
        description=data['description'],
        amount=float(data['amount']),
        record_type=FinancialRecordType(data['record_type']),
        record_date=parse_iso_datetime(data.get('record_date')),
        created_by=current_user.id,
    )
    db.session.add(record)
    log_action('finance.record.create', 'financial_record', None, company_id)
    db.session.commit()
    return api_ok({'id': record.id}, status=201)


@bp.get('/dashboard')
@login_required
def dashboard():
    company_id = request.args.get('company_id', type=int) or current_user.company_id
    if not company_id:
        return api_error('company_id_required')
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    token_stats = db.session.query(
        func.sum(TokenUsage.tokens_used),
        func.sum(TokenUsage.cost),
    ).filter(TokenUsage.company_id == company_id).one()

    income = db.session.query(func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.company_id == company_id,
        FinancialRecord.record_type == FinancialRecordType.INCOME,
    ).scalar() or 0
    expense = db.session.query(func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.company_id == company_id,
        FinancialRecord.record_type == FinancialRecordType.EXPENSE,
    ).scalar() or 0

    return api_ok(
        {
            'company_id': company_id,
            'tokens_used': int(token_stats[0] or 0),
            'ai_cost': float(token_stats[1] or 0),
            'income': float(income),
            'expense': float(expense),
            'profit': float(income - expense),
        }
    )
