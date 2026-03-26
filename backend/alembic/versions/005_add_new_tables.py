"""add_departments_dictionaries_approvals_remittances_declarations_logs

Revision ID: 005_add_new_tables
Revises: 004_add_project_documents
Create Date: 2026-03-26

"""

from alembic import op
import sqlalchemy as sa


revision = "005_add_new_tables"
down_revision = "004_add_project_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("department_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("department_name", sa.String(100), nullable=False),
        sa.Column("leader_user_id", sa.UUID(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.department_id"]),
        sa.PrimaryKeyConstraint("department_id"),
    )
    op.create_index("ix_departments_tenant_id", "departments", ["tenant_id"])

    op.create_table(
        "data_dictionaries",
        sa.Column("dict_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("dict_type", sa.String(50), nullable=False),
        sa.Column("dict_label", sa.String(100), nullable=False),
        sa.Column("dict_value", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("dict_id"),
    )
    op.create_index(
        "ix_data_dictionaries_tenant_id", "data_dictionaries", ["tenant_id"]
    )
    op.create_index(
        "ix_data_dictionaries_dict_type", "data_dictionaries", ["dict_type"]
    )

    op.create_table(
        "approval_flows",
        sa.Column("flow_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("current_level", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects_investment.project_id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("flow_id"),
    )
    op.create_index("ix_approval_flows_project_id", "approval_flows", ["project_id"])
    op.create_index("ix_approval_flows_tenant_id", "approval_flows", ["tenant_id"])

    op.create_table(
        "approval_logs",
        sa.Column("log_id", sa.UUID(), nullable=False),
        sa.Column("flow_id", sa.UUID(), nullable=False),
        sa.Column("approver_id", sa.UUID(), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("opinion", sa.Text(), nullable=True),
        sa.Column("operator_ip", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["flow_id"], ["approval_flows.flow_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index("ix_approval_logs_flow_id", "approval_logs", ["flow_id"])

    op.create_table(
        "remittance_records",
        sa.Column("record_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("remittance_amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("receiver_account_name", sa.String(255), nullable=False),
        sa.Column("receiver_bank_name", sa.String(255), nullable=False),
        sa.Column("receiver_account_no", sa.String(100), nullable=False),
        sa.Column("remittance_date", sa.DateTime(), nullable=False),
        sa.Column("voucher_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("registered_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects_investment.project_id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("record_id"),
    )
    op.create_index(
        "ix_remittance_records_project_id", "remittance_records", ["project_id"]
    )
    op.create_index(
        "ix_remittance_records_tenant_id", "remittance_records", ["tenant_id"]
    )

    op.create_table(
        "declaration_records",
        sa.Column("record_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("target", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("receipt_no", sa.String(100), nullable=True),
        sa.Column("receipt_data", sa.JSON(), nullable=True),
        sa.Column("submitted_by", sa.UUID(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects_investment.project_id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("record_id"),
    )
    op.create_index(
        "ix_declaration_records_project_id", "declaration_records", ["project_id"]
    )
    op.create_index(
        "ix_declaration_records_tenant_id", "declaration_records", ["tenant_id"]
    )

    op.create_table(
        "system_logs",
        sa.Column("log_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index("ix_system_logs_tenant_id", "system_logs", ["tenant_id"])
    op.create_index("ix_system_logs_user_id", "system_logs", ["user_id"])

    op.create_table(
        "login_logs",
        sa.Column("log_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("login_status", sa.String(20), nullable=False),
        sa.Column("fail_reason", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("login_method", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index("ix_login_logs_username", "login_logs", ["username"])
    op.create_index("ix_login_logs_created_at", "login_logs", ["created_at"])

    op.create_table(
        "sensitive_words",
        sa.Column("word_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("word_text", sa.String(100), nullable=False),
        sa.Column("word_type", sa.String(50), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("word_id"),
    )
    op.create_index("ix_sensitive_words_tenant_id", "sensitive_words", ["tenant_id"])

    op.add_column("tenants", sa.Column("uscc", sa.String(50), nullable=True))
    op.add_column(
        "tenants", sa.Column("legal_representative", sa.String(100), nullable=True)
    )
    op.add_column("tenants", sa.Column("registered_address", sa.Text(), nullable=True))

    op.add_column("users", sa.Column("phone", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("department_id", sa.UUID(), nullable=True))
    op.create_index("ix_users_department_id", "users", ["department_id"])
    op.create_foreign_key(
        "fk_users_department_id",
        "users",
        "departments",
        ["department_id"],
        ["department_id"],
    )

    op.add_column(
        "projects_investment", sa.Column("project_code", sa.String(50), nullable=True)
    )
    op.add_column(
        "projects_investment", sa.Column("is_submitted", sa.Integer(), nullable=True)
    )
    op.add_column(
        "projects_investment", sa.Column("submitted_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "projects_investment", sa.Column("submitted_by", sa.UUID(), nullable=True)
    )
    op.create_index(
        "ix_projects_investment_project_code", "projects_investment", ["project_code"]
    )
    op.create_index(
        "ix_projects_investment_tenant_id", "projects_investment", ["tenant_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_projects_investment_tenant_id", "projects_investment")
    op.drop_index("ix_projects_investment_project_code", "projects_investment")
    op.drop_column("projects_investment", "submitted_by")
    op.drop_column("projects_investment", "submitted_at")
    op.drop_column("projects_investment", "is_submitted")
    op.drop_column("projects_investment", "project_code")

    op.drop_constraint("fk_users_department_id", "users", type_="foreignkey")
    op.drop_index("ix_users_department_id", "users")
    op.drop_column("users", "department_id")
    op.drop_column("users", "phone")

    op.drop_column("tenants", "registered_address")
    op.drop_column("tenants", "legal_representative")
    op.drop_column("tenants", "uscc")

    op.drop_table("sensitive_words")
    op.drop_table("login_logs")
    op.drop_table("system_logs")
    op.drop_table("declaration_records")
    op.drop_table("remittance_records")
    op.drop_table("approval_logs")
    op.drop_table("approval_flows")
    op.drop_table("data_dictionaries")
    op.drop_table("departments")
