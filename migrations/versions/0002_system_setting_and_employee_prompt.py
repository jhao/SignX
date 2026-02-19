from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0002_system_setting_and_employee_prompt'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('employee', sa.Column('agent_prompt', sa.Text(), nullable=True))
    op.create_table(
        'system_setting',
        sa.Column('key', sa.String(length=128), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade() -> None:
    op.drop_table('system_setting')
    op.drop_column('employee', 'agent_prompt')
