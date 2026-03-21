"""add token columns to billing_logs

Revision ID: add_token_columns
Revises:
Create Date: 2026-03-21

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_token_columns"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "billing_logs",
        sa.Column("prompt_tokens", sa.Integer(), nullable=True, comment="输入token数"),
    )
    op.add_column(
        "billing_logs",
        sa.Column(
            "completion_tokens", sa.Integer(), nullable=True, comment="输出token数"
        ),
    )
    op.add_column(
        "billing_logs",
        sa.Column("total_tokens", sa.Integer(), nullable=True, comment="总token数"),
    )


def downgrade() -> None:
    op.drop_column("billing_logs", "total_tokens")
    op.drop_column("billing_logs", "completion_tokens")
    op.drop_column("billing_logs", "prompt_tokens")
