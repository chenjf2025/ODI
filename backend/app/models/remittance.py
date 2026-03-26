import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class RemittanceRecord(Base):
    __tablename__ = "remittance_records"

    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects_investment.project_id"), nullable=False
    )
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )

    remittance_amount = Column(Numeric(20, 2), nullable=False, comment="付汇金额")
    currency = Column(String(10), default="USD", comment="币种")
    receiver_account_name = Column(String(255), nullable=False, comment="收款账户名")
    receiver_bank_name = Column(String(255), nullable=False, comment="收款银行名称")
    receiver_account_no = Column(String(100), nullable=False, comment="收款账号")
    remittance_date = Column(DateTime, nullable=False, comment="付汇日期")

    voucher_url = Column(String(500), nullable=True, comment="付汇凭证URL")

    status = Column(String(20), default="PENDING", comment="状态: PENDING/COMPLETED")
    registered_by = Column(UUID(as_uuid=True), nullable=False, comment="登记人")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("ProjectInvestment", back_populates="remittance_records")
    tenant = relationship("Tenant", back_populates="remittance_records")
