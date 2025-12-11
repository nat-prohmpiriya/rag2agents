"""add_workflow_tables

Revision ID: e1f2g3h4i5j6
Revises: d877b82a9bb3
Create Date: 2025-12-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e1f2g3h4i5j6'
down_revision: Union[str, None] = 'd877b82a9bb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('nodes', postgresql.JSON(), nullable=True, default=[]),
        sa.Column('edges', postgresql.JSON(), nullable=True, default=[]),
        sa.Column('viewport', postgresql.JSON(), nullable=True, default={}),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('is_template', sa.Boolean(), nullable=False, default=False),
        sa.Column('config', postgresql.JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_workflows_user_id', 'workflows', ['user_id'])
    op.create_index('ix_workflows_status', 'workflows', ['status'])

    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('inputs', postgresql.JSON(), nullable=True, default={}),
        sa.Column('outputs', postgresql.JSON(), nullable=True, default={}),
        sa.Column('node_states', postgresql.JSON(), nullable=True, default={}),
        sa.Column('current_node_id', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('logs', postgresql.JSON(), nullable=True, default=[]),
        sa.Column('started_at', sa.String(50), nullable=True),
        sa.Column('completed_at', sa.String(50), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('ix_workflow_executions_user_id', 'workflow_executions', ['user_id'])
    op.create_index('ix_workflow_executions_status', 'workflow_executions', ['status'])


def downgrade() -> None:
    op.drop_index('ix_workflow_executions_status', table_name='workflow_executions')
    op.drop_index('ix_workflow_executions_user_id', table_name='workflow_executions')
    op.drop_index('ix_workflow_executions_workflow_id', table_name='workflow_executions')
    op.drop_table('workflow_executions')

    op.drop_index('ix_workflows_status', table_name='workflows')
    op.drop_index('ix_workflows_user_id', table_name='workflows')
    op.drop_table('workflows')
