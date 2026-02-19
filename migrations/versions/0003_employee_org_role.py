from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_employee_org_role'
down_revision = '0002_system_setting_and_employee_prompt'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('employee') as batch_op:
        batch_op.add_column(sa.Column('organization_role', sa.String(length=128), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('employee') as batch_op:
        batch_op.drop_column('organization_role')
