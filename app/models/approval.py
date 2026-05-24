"""审批记录模型"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.utils.database import Base


class ApprovalAction(str, enum.Enum):
    submit = "submit"        # 提交审核
    approve = "approve"      # 批准
    reject = "reject"        # 驳回
    publish = "publish"      # 发布
    archive = "archive"      # 归档
    recall = "recall"        # 撤回


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )
    action = Column(
        SAEnum(ApprovalAction, name="approval_action"),
        nullable=False,
        comment="操作类型",
    )
    comments = Column(Text, comment="审批意见")
    operator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # 关联
    document = relationship("Document", back_populates="approval_records")
    operator = relationship("User", lazy="joined")
