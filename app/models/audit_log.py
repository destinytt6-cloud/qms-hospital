"""审计日志模型"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.utils.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False, comment="操作: create/update/delete/approve/reject/publish/login")
    target_type = Column(String(50), nullable=False, comment="操作对象类型: document/user/category/department")
    target_id = Column(String(100), comment="操作对象ID")
    details = Column(Text, comment="详细信息(JSON)")
    ip_address = Column(String(45), comment="客户端IP")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # 关联
    user = relationship("User", lazy="joined")
