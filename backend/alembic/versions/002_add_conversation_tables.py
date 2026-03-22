"""add_conversation_tables

Revision ID: add_conversation_tables
Revises: 001_add_token_columns
Create Date: 2026-03-22

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON

revision = "add_conversation_tables"
down_revision = "001_add_token_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conversation_sessions",
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.tenant_id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("is_deleted", sa.Integer(), server_default="0", nullable=True),
    )
    op.create_index("ix_conv_sessions_tenant", "conversation_sessions", ["tenant_id"])
    op.create_index("ix_conv_sessions_user", "conversation_sessions", ["user_id"])

    op.create_table(
        "conversation_messages",
        sa.Column(
            "message_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("conversation_sessions.session_id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("confidence", sa.String(10), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
    )
    op.create_index("ix_conv_messages_session", "conversation_messages", ["session_id"])

    op.create_table(
        "conversation_feedbacks",
        sa.Column(
            "feedback_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("conversation_sessions.session_id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column("rating", sa.String(10), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
    )
    op.create_index(
        "ix_conv_feedbacks_session", "conversation_feedbacks", ["session_id"]
    )


def downgrade():
    op.drop_table("conversation_feedbacks")
    op.drop_table("conversation_messages")
    op.drop_table("conversation_sessions")
