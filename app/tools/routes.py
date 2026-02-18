from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from ..api_utils import api_error, api_ok, ensure_company_scope, log_action
from ..extensions import db
from ..models import Tool
from . import bp


@bp.post('')
@login_required
def create_tool():
    data = request.get_json() or {}
    required = {'company_id', 'name'}
    if not required.issubset(data):
        return api_error('invalid_payload')
    company_id = int(data['company_id'])
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    tool = Tool(
        company_id=company_id,
        name=data['name'],
        description=data.get('description'),
        config=data.get('config', {}),
        supported_by_mcp=bool(data.get('supported_by_mcp', False)),
        created_by=current_user.id,
    )
    db.session.add(tool)
    log_action('tool.create', 'tool', None, company_id, {'name': tool.name})
    db.session.commit()
    return api_ok({'id': tool.id, 'name': tool.name}, status=201)


@bp.get('')
@login_required
def list_tools():
    company_id = request.args.get('company_id', type=int) or current_user.company_id
    if not company_id:
        return api_error('company_id_required')
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    tools = Tool.query.filter_by(company_id=company_id).order_by(Tool.id.desc()).all()
    return api_ok([
        {
            'id': tool.id,
            'name': tool.name,
            'description': tool.description,
            'supported_by_mcp': tool.supported_by_mcp,
            'config': tool.config,
            'updated_at': tool.updated_at.isoformat() if tool.updated_at else None,
        }
        for tool in tools
    ])


@bp.put('/<int:tool_id>')
@login_required
def update_tool(tool_id: int):
    data = request.get_json() or {}
    tool = Tool.query.get_or_404(tool_id)
    if not ensure_company_scope(tool.company_id):
        return api_error('forbidden', status=403)

    if 'name' in data:
        tool.name = data['name']
    if 'description' in data:
        tool.description = data.get('description')
    if 'config' in data:
        tool.config = data.get('config') or {}
    if 'supported_by_mcp' in data:
        tool.supported_by_mcp = bool(data.get('supported_by_mcp'))

    log_action('tool.update', 'tool', str(tool.id), tool.company_id, {'name': tool.name})
    db.session.commit()
    return api_ok({'id': tool.id, 'name': tool.name})


@bp.post('/openclaw/execute')
@login_required
def execute_openclaw():
    data = request.get_json() or {}
    company_id = int(data.get('company_id') or (current_user.company_id or 0))
    if not company_id:
        return api_error('company_id_required')
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    task_name = data.get('task_name', 'default_task')
    payload = data.get('payload', {})
    log_action('tool.openclaw.execute', 'tool_task', None, company_id, {'task_name': task_name, 'payload': payload})
    db.session.commit()
    return api_ok({'task_name': task_name, 'status': 'queued'})
