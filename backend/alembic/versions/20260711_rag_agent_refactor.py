"""rag_agent_refactor

Revision ID: 20260711rag
Revises: 423efa013cf2
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260711rag"
down_revision: Union[str, Sequence[str], None] = "423efa013cf2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("knowledge_bases", sa.Column("scope_type", sa.String(length=16), nullable=False, server_default="personal"))
    op.add_column("knowledge_bases", sa.Column("scope_id", sa.String(length=64), nullable=True))
    op.add_column("knowledge_bases", sa.Column("category", sa.String(length=80), nullable=False, server_default=""))
    op.add_column("knowledge_bases", sa.Column("tags", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("knowledge_bases", sa.Column("freshness_policy", sa.String(length=32), nullable=False, server_default="manual"))
    op.add_column("knowledge_bases", sa.Column("last_indexed_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_knowledge_bases_scope_type"), "knowledge_bases", ["scope_type"], unique=False)
    op.create_index(op.f("ix_knowledge_bases_scope_id"), "knowledge_bases", ["scope_id"], unique=False)

    op.add_column("knowledge_documents", sa.Column("version_sha", sa.String(length=64), nullable=False, server_default=""))
    op.add_column("knowledge_documents", sa.Column("error_message", sa.Text(), nullable=False, server_default=""))

    op.create_table(
        "knowledge_conversations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("kb_id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["kb_id"], ["knowledge_bases.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_conversations_kb_id"), "knowledge_conversations", ["kb_id"], unique=False)
    op.create_index(op.f("ix_knowledge_conversations_owner_id"), "knowledge_conversations", ["owner_id"], unique=False)
    op.create_table(
        "knowledge_messages",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["knowledge_conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_messages_conversation_id"), "knowledge_messages", ["conversation_id"], unique=False)
    op.create_table(
        "knowledge_citation_snapshots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("page_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("paragraph_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["knowledge_messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_citation_snapshots_message_id"), "knowledge_citation_snapshots", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_citation_snapshots_message_id"), table_name="knowledge_citation_snapshots")
    op.drop_table("knowledge_citation_snapshots")
    op.drop_index(op.f("ix_knowledge_messages_conversation_id"), table_name="knowledge_messages")
    op.drop_table("knowledge_messages")
    op.drop_index(op.f("ix_knowledge_conversations_owner_id"), table_name="knowledge_conversations")
    op.drop_index(op.f("ix_knowledge_conversations_kb_id"), table_name="knowledge_conversations")
    op.drop_table("knowledge_conversations")

    op.drop_column("knowledge_documents", "error_message")
    op.drop_column("knowledge_documents", "version_sha")

    op.drop_index(op.f("ix_knowledge_bases_scope_id"), table_name="knowledge_bases")
    op.drop_index(op.f("ix_knowledge_bases_scope_type"), table_name="knowledge_bases")
    op.drop_column("knowledge_bases", "last_indexed_at")
    op.drop_column("knowledge_bases", "freshness_policy")
    op.drop_column("knowledge_bases", "tags")
    op.drop_column("knowledge_bases", "category")
    op.drop_column("knowledge_bases", "scope_id")
    op.drop_column("knowledge_bases", "scope_type")
