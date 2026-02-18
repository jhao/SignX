from __future__ import annotations

import enum
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db, login_manager


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class PlatformRole(enum.StrEnum):
    PLATFORM_ADMIN = 'platform_admin'
    USER = 'user'


class CompanyRole(enum.StrEnum):
    OWNER = 'owner'
    FINANCE_MANAGER = 'finance_manager'
    HR_MANAGER = 'hr_manager'
    PROJECT_LEAD = 'project_lead'
    MEMBER = 'member'


class TaskStatus(enum.StrEnum):
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    BLOCKED = 'blocked'
    DONE = 'done'


class Priority(enum.StrEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class FinancialRecordType(enum.StrEnum):
    INCOME = 'income'
    EXPENSE = 'expense'


class UserAccount(db.Model, UserMixin, TimestampMixin):
    __tablename__ = 'user_account'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(db.String(128), nullable=False)
    platform_role: Mapped[PlatformRole] = mapped_column(Enum(PlatformRole), default=PlatformRole.USER)
    company_id: Mapped[int | None] = mapped_column(ForeignKey('company.id'))
    is_active: Mapped[bool] = mapped_column(default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(default=None)

    company: Mapped['Company | None'] = relationship(
        back_populates='accounts',
        foreign_keys=[company_id],
    )


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(UserAccount, int(user_id))


class Company(db.Model, TimestampMixin):
    __tablename__ = 'company'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(128), nullable=False, unique=True)
    business_model: Mapped[str | None] = mapped_column(db.String(128))
    description: Mapped[str | None] = mapped_column(db.Text)
    accounting_method: Mapped[str | None] = mapped_column(db.String(64))
    capital: Mapped[float | None] = mapped_column(db.Float)
    tax_info: Mapped[str | None] = mapped_column(db.Text)
    organization_structure: Mapped[str | None] = mapped_column(db.Text)
    goals: Mapped[str | None] = mapped_column(db.Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))

    accounts: Mapped[list['UserAccount']] = relationship(
        back_populates='company',
        foreign_keys='UserAccount.company_id',
    )
    employees: Mapped[list['Employee']] = relationship(back_populates='company', cascade='all, delete-orphan')
    projects: Mapped[list['Project']] = relationship(back_populates='company', cascade='all, delete-orphan')


class Role(db.Model, TimestampMixin):
    __tablename__ = 'role'
    __table_args__ = (UniqueConstraint('company_id', 'name', name='uq_role_company_name'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('company.id'), nullable=False)
    name: Mapped[str] = mapped_column(db.String(64), nullable=False)
    responsibilities: Mapped[str | None] = mapped_column(db.Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))


class Employee(db.Model, TimestampMixin):
    __tablename__ = 'employee'

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('company.id'), nullable=False)
    name: Mapped[str] = mapped_column(db.String(128), nullable=False)
    primary_tasks: Mapped[str | None] = mapped_column(db.Text)
    role_id: Mapped[int | None] = mapped_column(ForeignKey('role.id'))
    company_role: Mapped[CompanyRole] = mapped_column(Enum(CompanyRole), default=CompanyRole.MEMBER)
    ai_provider: Mapped[str | None] = mapped_column(db.String(64))
    api_key_encrypted: Mapped[str | None] = mapped_column(db.String(512))
    photo_path: Mapped[str | None] = mapped_column(db.String(255))
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))

    company: Mapped['Company'] = relationship(back_populates='employees')


class Project(db.Model, TimestampMixin):
    __tablename__ = 'project'

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('company.id'), nullable=False)
    name: Mapped[str] = mapped_column(db.String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(db.Text)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey('employee.id'))
    start_date: Mapped[datetime | None] = mapped_column(db.DateTime)
    end_date: Mapped[datetime | None] = mapped_column(db.DateTime)
    objective: Mapped[str | None] = mapped_column(db.Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))

    company: Mapped['Company'] = relationship(back_populates='projects')
    tasks: Mapped[list['Task']] = relationship(back_populates='project', cascade='all, delete-orphan')


class Task(db.Model, TimestampMixin):
    __tablename__ = 'task'

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('project.id'), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey('employee.id'))
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    due_date: Mapped[datetime | None] = mapped_column(db.DateTime)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.MEDIUM)
    dependency_task_id: Mapped[int | None] = mapped_column(ForeignKey('task.id'))
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))

    project: Mapped['Project'] = relationship(back_populates='tasks')


class TokenUsage(db.Model, TimestampMixin):
    __tablename__ = 'token_usage'

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('company.id'), nullable=False)
    model: Mapped[str] = mapped_column(db.String(64), nullable=False)
    tokens_used: Mapped[int] = mapped_column(nullable=False)
    cost: Mapped[float] = mapped_column(db.Float, nullable=False)
    usage_date: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))


class FinancialRecord(db.Model, TimestampMixin):
    __tablename__ = 'financial_record'

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('company.id'), nullable=False)
    record_date: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    amount: Mapped[float] = mapped_column(db.Float, nullable=False)
    record_type: Mapped[FinancialRecordType] = mapped_column(Enum(FinancialRecordType), nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))


class Tool(db.Model, TimestampMixin):
    __tablename__ = 'tool'

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('company.id'), nullable=False)
    name: Mapped[str] = mapped_column(db.String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(db.Text)
    config: Mapped[dict] = mapped_column(db.JSON, default=dict)
    supported_by_mcp: Mapped[bool] = mapped_column(default=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))


class ProjectEmployee(db.Model, TimestampMixin):
    __tablename__ = 'project_employee'

    project_id: Mapped[int] = mapped_column(ForeignKey('project.id'), primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employee.id'), primary_key=True)
    role_in_project: Mapped[str | None] = mapped_column(db.String(64))
    created_by: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))


class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey('company.id'))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey('user_account.id'))
    action: Mapped[str] = mapped_column(db.String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(db.String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(db.String(64))
    details: Mapped[dict] = mapped_column(db.JSON, default=dict)
    ip_address: Mapped[str | None] = mapped_column(db.String(64))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
