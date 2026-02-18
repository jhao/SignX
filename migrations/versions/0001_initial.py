from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


platform_role_enum = sa.Enum('platform_admin', 'user', name='platformrole')
company_role_enum = sa.Enum('owner', 'finance_manager', 'hr_manager', 'project_lead', 'member', name='companyrole')
task_status_enum = sa.Enum('todo', 'in_progress', 'blocked', 'done', name='taskstatus')
priority_enum = sa.Enum('low', 'medium', 'high', 'urgent', name='priority')
financial_record_type_enum = sa.Enum('income', 'expense', name='financialrecordtype')


def upgrade() -> None:
    bind = op.get_bind()
    platform_role_enum.create(bind, checkfirst=True)
    company_role_enum.create(bind, checkfirst=True)
    task_status_enum.create(bind, checkfirst=True)
    priority_enum.create(bind, checkfirst=True)
    financial_record_type_enum.create(bind, checkfirst=True)

    op.create_table(
        'company',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('business_model', sa.String(length=128), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('accounting_method', sa.String(length=64), nullable=True),
        sa.Column('capital', sa.Float(), nullable=True),
        sa.Column('tax_info', sa.Text(), nullable=True),
        sa.Column('organization_structure', sa.Text(), nullable=True),
        sa.Column('goals', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'user_account',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=False),
        sa.Column('platform_role', platform_role_enum, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_foreign_key('fk_company_created_by', 'company', 'user_account', ['created_by'], ['id'])

    op.create_table(
        'role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'name', name='uq_role_company_name')
    )

    op.create_table(
        'employee',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('primary_tasks', sa.Text(), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.Column('company_role', company_role_enum, nullable=False),
        sa.Column('ai_provider', sa.String(length=64), nullable=True),
        sa.Column('api_key_encrypted', sa.String(length=512), nullable=True),
        sa.Column('photo_path', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.id']),
        sa.ForeignKeyConstraint(['role_id'], ['role.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('objective', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.id']),
        sa.ForeignKeyConstraint(['lead_id'], ['employee.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'task',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('priority', priority_enum, nullable=False),
        sa.Column('dependency_task_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignee_id'], ['employee.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.id']),
        sa.ForeignKeyConstraint(['dependency_task_id'], ['task.id']),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'token_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('model', sa.String(length=64), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('usage_date', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'financial_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('record_date', sa.DateTime(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('record_type', financial_record_type_enum, nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tool',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('supported_by_mcp', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'project_employee',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('role_in_project', sa.String(length=64), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user_account.id']),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id']),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('project_id', 'employee_id')
    )

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=64), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['user_account.id']),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('project_employee')
    op.drop_table('tool')
    op.drop_table('financial_record')
    op.drop_table('token_usage')
    op.drop_table('task')
    op.drop_table('project')
    op.drop_table('employee')
    op.drop_table('role')
    op.drop_constraint('fk_company_created_by', 'company', type_='foreignkey')
    op.drop_table('user_account')
    op.drop_table('company')

    bind = op.get_bind()
    financial_record_type_enum.drop(bind, checkfirst=True)
    priority_enum.drop(bind, checkfirst=True)
    task_status_enum.drop(bind, checkfirst=True)
    company_role_enum.drop(bind, checkfirst=True)
    platform_role_enum.drop(bind, checkfirst=True)
