"""durable workflow debug sessions

Revision ID: 20260716wfdebug
Revises: 20260716workflow
Create Date: 2026-07-16 21:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260716wfdebug"
down_revision: Union[str, Sequence[str], None] = "20260716workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_debug_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_token", sa.String(length=64), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("nodes_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("edges_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("inputs_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("node_outputs_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("results_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_debug_sessions_workflow_id"), "workflow_debug_sessions", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_workflow_debug_sessions_owner_id"), "workflow_debug_sessions", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_debug_sessions_owner_id"), table_name="workflow_debug_sessions")
    op.drop_index(op.f("ix_workflow_debug_sessions_workflow_id"), table_name="workflow_debug_sessions")
    op.drop_table("workflow_debug_sessions")
