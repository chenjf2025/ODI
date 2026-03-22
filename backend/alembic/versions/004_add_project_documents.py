"""add project documents table

Revision ID: 004_add_project_documents
Revises: 003_add_cascade_delete
Create Date: 2026-03-23

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "004_add_project_documents"
down_revision = "003_add_cascade_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_documents",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("step_status", sa.String(50), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_size", sa.String(50), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("review_result", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(20), nullable=True),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects_investment.project_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("document_id"),
    )
    op.create_index(
        "ix_project_documents_project_id", "project_documents", ["project_id"]
    )
    op.create_index(
        "ix_project_documents_step_status", "project_documents", ["step_status"]
    )


def downgrade() -> None:
    op.drop_table("project_documents")
