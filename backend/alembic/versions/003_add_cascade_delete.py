"""add_cascade_delete_to_project_status_logs

Revision ID: 003_add_cascade_delete
Revises: 002_add_conversation_tables
Create Date: 2026-03-23

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "003_add_cascade_delete"
down_revision = "002_add_conversation_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE project_status_logs DROP CONSTRAINT IF EXISTS project_status_logs_project_id_fkey"
    )
    op.execute(
        "ALTER TABLE project_status_logs ADD CONSTRAINT project_status_logs_project_id_fkey "
        "FOREIGN KEY (project_id) REFERENCES projects_investment(project_id) ON DELETE CASCADE"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE project_status_logs DROP CONSTRAINT IF EXISTS project_status_logs_project_id_fkey"
    )
    op.execute(
        "ALTER TABLE project_status_logs ADD CONSTRAINT project_status_logs_project_id_fkey "
        "FOREIGN KEY (project_id) REFERENCES projects_investment(project_id)"
    )
