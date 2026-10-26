"""add_data_provenance_and_job_execution

Revision ID: c1a9f3b8d4e2
Revises: 289f79484c68
Create Date: 2026-10-26 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a9f3b8d4e2'
down_revision: Union[str, Sequence[str], None] = '289f79484c68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add provenance fields to institutions
    with op.batch_alter_table('institutions') as batch_op:
        batch_op.add_column(sa.Column('source_system', sa.String(50), nullable=False, server_default='SETU_OPERATIONAL'))
        batch_op.add_column(sa.Column('external_id', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('source_record_version', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('source_updated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('synced_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        batch_op.add_column(sa.Column('sync_status', sa.String(50), nullable=False, server_default='SYNCED'))
        batch_op.add_column(sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('last_sync_error', sa.Text(), nullable=True))
        batch_op.create_index('ix_institutions_external_id', ['external_id'], unique=False)

    # 2. Add provenance fields to applications
    with op.batch_alter_table('applications') as batch_op:
        batch_op.add_column(sa.Column('source_system', sa.String(50), nullable=False, server_default='SETU_OPERATIONAL'))
        batch_op.add_column(sa.Column('external_id', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('source_record_version', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('source_updated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('synced_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        batch_op.add_column(sa.Column('sync_status', sa.String(50), nullable=False, server_default='SYNCED'))
        batch_op.add_column(sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('last_sync_error', sa.Text(), nullable=True))
        batch_op.create_index('ix_applications_external_id', ['external_id'], unique=False)

    # 3. Create job_executions table
    op.create_table(
        'job_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_name', sa.String(100), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='RUNNING', index=True),
        sa.Column('items_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )


def downgrade() -> None:
    op.drop_table('job_executions')

    with op.batch_alter_table('applications') as batch_op:
        batch_op.drop_index('ix_applications_external_id')
        batch_op.drop_column('last_sync_error')
        batch_op.drop_column('is_synthetic')
        batch_op.drop_column('sync_status')
        batch_op.drop_column('synced_at')
        batch_op.drop_column('source_updated_at')
        batch_op.drop_column('source_record_version')
        batch_op.drop_column('external_id')
        batch_op.drop_column('source_system')

    with op.batch_alter_table('institutions') as batch_op:
        batch_op.drop_index('ix_institutions_external_id')
        batch_op.drop_column('last_sync_error')
        batch_op.drop_column('is_synthetic')
        batch_op.drop_column('sync_status')
        batch_op.drop_column('synced_at')
        batch_op.drop_column('source_updated_at')
        batch_op.drop_column('source_record_version')
        batch_op.drop_column('external_id')
        batch_op.drop_column('source_system')

