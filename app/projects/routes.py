from __future__ import annotations

import json

from flask import request
from flask_login import current_user, login_required

from ..ai_service import generate_structured_chat_completion
from ..api_utils import api_error, api_ok, ensure_company_scope, log_action, parse_iso_datetime
from ..extensions import db
from ..models import Employee, Priority, Project, ProjectEmployee, Task, TaskStatus, Tool
from . import bp


@bp.post('')
@login_required
def create_project():
    data = request.get_json() or {}
    if not {'company_id', 'name'}.issubset(data):
        return api_error('invalid_payload')
    company_id = int(data['company_id'])
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    lead_id = data.get('lead_id')
    if lead_id:
        lead = Employee.query.filter_by(id=lead_id, company_id=company_id).first()
        if not lead:
            return api_error('lead_employee_not_found')

    objective = data.get('objective')
    project = Project(
        company_id=company_id,
        name=data['name'],
        description=data.get('description'),
        lead_id=lead_id,
        start_date=parse_iso_datetime(data.get('start_date')),
        end_date=parse_iso_datetime(data.get('end_date')),
        objective=objective,
        created_by=current_user.id,
    )
    db.session.add(project)
    db.session.flush()

    if objective and data.get('auto_breakdown', True):
        try:
            plan_text = generate_structured_chat_completion(
                system_prompt='你是企业项目经理，输出任务拆解JSON。',
                user_prompt=(
                    '请按以下目标输出 JSON 数组，每项包括 description, priority(low/medium/high), status(todo)。'
                    f'\n项目：{project.name}\n目标：{objective}'
                ),
            )
            start_index = plan_text.find('[')
            end_index = plan_text.rfind(']')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                parsed = json.loads(plan_text[start_index : end_index + 1])
                if isinstance(parsed, list):
                    for item in parsed:
                        if not isinstance(item, dict) or not item.get('description'):
                            continue
                        db.session.add(
                            Task(
                                project_id=project.id,
                                description=item['description'],
                                status=TaskStatus(item.get('status', TaskStatus.TODO.value)),
                                priority=Priority(item.get('priority', Priority.MEDIUM.value)),
                                created_by=current_user.id,
                            )
                        )
        except Exception:
            pass

    log_action('project.create', 'project', str(project.id), company_id, {'name': project.name})
    db.session.commit()
    return api_ok({'id': project.id, 'name': project.name}, status=201)


@bp.get('')
@login_required
def list_projects():
    company_id = request.args.get('company_id', type=int) or current_user.company_id
    if not company_id:
        return api_error('company_id_required')
    if not ensure_company_scope(company_id):
        return api_error('forbidden', status=403)

    projects = Project.query.filter_by(company_id=company_id).order_by(Project.id.desc()).all()
    employee_map = {e.id: e for e in Employee.query.filter_by(company_id=company_id).all()}
    return api_ok(
        [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'lead_id': p.lead_id,
                'objective': p.objective,
                'lead_display': (
                    f"{employee_map[p.lead_id].name}（{employee_map[p.lead_id].organization_role or employee_map[p.lead_id].company_role.value}）"
                    if p.lead_id in employee_map
                    else None
                ),
            }
            for p in projects
        ]
    )


@bp.post('/<int:project_id>/tasks')
@login_required
def create_task(project_id: int):
    project = Project.query.get_or_404(project_id)
    if not ensure_company_scope(project.company_id):
        return api_error('forbidden', status=403)
    data = request.get_json() or {}
    if 'description' not in data:
        return api_error('invalid_payload')

    assignee_id = data.get('assignee_id')
    if assignee_id:
        assignee = Employee.query.filter_by(id=assignee_id, company_id=project.company_id).first()
        if not assignee:
            return api_error('assignee_not_found')

    task = Task(
        project_id=project_id,
        assignee_id=assignee_id,
        description=data['description'],
        status=TaskStatus(data.get('status', TaskStatus.TODO.value)),
        due_date=parse_iso_datetime(data.get('due_date')),
        priority=Priority(data.get('priority', Priority.MEDIUM.value)),
        dependency_task_id=data.get('dependency_task_id'),
        created_by=current_user.id,
    )
    db.session.add(task)
    log_action('task.create', 'task', None, project.company_id, {'project_id': project.id})
    db.session.commit()
    return api_ok({'id': task.id, 'status': task.status.value}, status=201)


@bp.get('/<int:project_id>/tasks')
@login_required
def list_tasks(project_id: int):
    project = Project.query.get_or_404(project_id)
    if not ensure_company_scope(project.company_id):
        return api_error('forbidden', status=403)
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.id.desc()).all()
    employee_map = {e.id: e for e in Employee.query.filter_by(company_id=project.company_id).all()}
    return api_ok(
        [
            {
                'id': t.id,
                'description': t.description,
                'status': t.status.value,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'priority': t.priority.value,
                'assignee_id': t.assignee_id,
                'assignee_display': (
                    f"{employee_map[t.assignee_id].name}（{employee_map[t.assignee_id].organization_role or employee_map[t.assignee_id].company_role.value}）"
                    if t.assignee_id in employee_map
                    else None
                ),
                'dependency_task_id': t.dependency_task_id,
            }
            for t in tasks
        ]
    )


@bp.post('/tasks/<int:task_id>/execute')
@login_required
def execute_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    project = Project.query.get_or_404(task.project_id)
    if not ensure_company_scope(project.company_id):
        return api_error('forbidden', status=403)
    if not task.assignee_id:
        return api_error('assignee_not_found')

    assignee = Employee.query.filter_by(id=task.assignee_id, company_id=project.company_id).first()
    if not assignee:
        return api_error('assignee_not_found')

    tools = Tool.query.filter_by(company_id=project.company_id, supported_by_mcp=True).all()
    mcp_tools = [{'name': t.name, 'description': t.description, 'config': t.config} for t in tools]
    context = [
        {'id': t.id, 'description': t.description, 'status': t.status.value, 'priority': t.priority.value}
        for t in Task.query.filter_by(project_id=project.id).order_by(Task.id.asc()).all()
    ]

    try:
        plan = generate_structured_chat_completion(
            system_prompt='你是任务执行编排助手，需要产出可执行的事件动作清单JSON数组。',
            user_prompt=(
                f'员工:{assignee.name}，组织角色:{assignee.organization_role or assignee.company_role.value}。'
                f'员工提示词:{assignee.agent_prompt or "未提供"}。\n'
                f'当前任务:{task.description}\n'
                f'项目上下文:{json.dumps(context, ensure_ascii=False)}\n'
                f'MCP工具清单:{json.dumps(mcp_tools, ensure_ascii=False)}\n'
                '请输出JSON数组，每项包含 event, action, tool_name, input。'
            ),
        )
    except ValueError as exc:
        if str(exc) == 'ai_model_not_configured':
            return api_error('ai_model_not_configured')
        raise
    except Exception:
        return api_error('task_execution_plan_failed', status=502)

    log_action('task.execute.plan', 'task', str(task.id), project.company_id, {'task_id': task.id})
    db.session.commit()
    return api_ok({'task_id': task.id, 'plan': plan, 'mcp_tools': mcp_tools})


@bp.post('/<int:project_id>/members')
@login_required
def assign_project_member(project_id: int):
    project = Project.query.get_or_404(project_id)
    if not ensure_company_scope(project.company_id):
        return api_error('forbidden', status=403)
    data = request.get_json() or {}
    if 'employee_id' not in data:
        return api_error('invalid_payload')

    member = Employee.query.filter_by(id=data['employee_id'], company_id=project.company_id).first()
    if not member:
        return api_error('employee_not_found')

    project_member = ProjectEmployee(
        project_id=project_id,
        employee_id=data['employee_id'],
        role_in_project=data.get('role_in_project'),
        created_by=current_user.id,
    )
    db.session.merge(project_member)
    log_action('project.member.assign', 'project_employee', None, project.company_id, {'project_id': project_id})
    db.session.commit()
    return api_ok({'project_id': project_id, 'employee_id': data['employee_id']}, status=201)
