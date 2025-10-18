from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_table(
        'envelope',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'sent', 'viewed', 'signed', 'completed', 'voided', name='envelopestatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'document',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('envelope_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_path', sa.String(length=512), nullable=False),
        sa.Column('pdf_path', sa.String(length=512), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['envelope_id'], ['envelope.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'signer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('envelope_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('access_code', sa.String(length=64), nullable=True),
        sa.Column('invite_token', sa.String(length=128), nullable=True),
        sa.Column('has_signed', sa.Boolean(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['envelope_id'], ['envelope.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invite_token')
    )
    op.create_table(
        'audit_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('envelope_id', sa.Integer(), nullable=False),
        sa.Column('signer_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['envelope_id'], ['envelope.id'], ),
        sa.ForeignKeyConstraint(['signer_id'], ['signer.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'notification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('signer_id', sa.Integer(), nullable=True),
        sa.Column('envelope_id', sa.Integer(), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['envelope_id'], ['envelope.id'], ),
        sa.ForeignKeyConstraint(['signer_id'], ['signer.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'field',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('signer_id', sa.Integer(), nullable=False),
        sa.Column('field_type', sa.String(length=32), nullable=False),
        sa.Column('page', sa.Integer(), nullable=True),
        sa.Column('x', sa.Float(), nullable=False),
        sa.Column('y', sa.Float(), nullable=False),
        sa.Column('width', sa.Float(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
        sa.ForeignKeyConstraint(['signer_id'], ['signer.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'signature',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('signer_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('image_data', sa.LargeBinary(), nullable=True),
        sa.Column('stamp_path', sa.String(length=512), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
        sa.ForeignKeyConstraint(['field_id'], ['field.id'], ),
        sa.ForeignKeyConstraint(['signer_id'], ['signer.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'crypto_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('signature_id', sa.Integer(), nullable=False),
        sa.Column('algorithm', sa.String(length=64), nullable=False),
        sa.Column('certificate_subject', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('signature_bytes', sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(['signature_id'], ['signature.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'roles_users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'role')
    )


def downgrade() -> None:
    op.drop_table('roles_users')
    op.drop_table('crypto_record')
    op.drop_table('signature')
    op.drop_table('field')
    op.drop_table('notification')
    op.drop_table('audit_event')
    op.drop_table('signer')
    op.drop_table('document')
    op.drop_table('envelope')
    op.drop_table('user')
    op.execute("DROP TYPE IF EXISTS envelopestatus")
