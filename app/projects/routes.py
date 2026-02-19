from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from ..api_utils import api_error, api_ok, ensure_company_scope, log_action, parse_iso_datetime
from ..extensions import db
from ..models import Employee, Priority, Project, ProjectEmployee, Task, TaskStatus
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

    project = Project(
        company_id=company_id,
        name=data['name'],
        description=data.get('description'),
        lead_id=lead_id,
        start_date=parse_iso_datetime(data.get('start_date')),
        end_date=parse_iso_datetime(data.get('end_date')),
        objective=data.get('objective'),
        created_by=current_user.id,
    )
    db.session.add(project)
    db.session.flush()
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
    return api_ok([
        {
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'lead_id': p.lead_id,
            'objective': p.objective,
        }
        for p in projects
    ])


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
    return api_ok([
        {
            'id': t.id,
            'description': t.description,
            'status': t.status.value,
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'priority': t.priority.value,
            'assignee_id': t.assignee_id,
            'dependency_task_id': t.dependency_task_id,
        }
        for t in tasks
    ])


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
