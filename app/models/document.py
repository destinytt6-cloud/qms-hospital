"""文件主模型 + 文件版本模型"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, BigInteger,
    Boolean, DateTime, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.utils.database import Base


class DocumentStatus(str, enum.Enum):
    draft = "draft"          # 起草中
    review = "review"        # 审核中
    approved = "approved"    # 已批准
    published = "published"  # 已发布
    archived = "archived"    # 已归档
    obsolete = "obsolete"    # 已废止


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False, comment="文件标题")
    document_code = Column(String(50), unique=True, nullable=False, comment="文件编号")
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_categories.id"),
        comment="文件分类",
    )
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id"),
        comment="归属科室",
    )
    version = Column(Integer, default=1, comment="当前版本号")
    status = Column(
        SAEnum(DocumentStatus, name="document_status"),
        default=DocumentStatus.draft,
        nullable=False,
        comment="状态",
    )
    description = Column(Text, comment="摘要/描述")
    keywords = Column(String(200), comment="关键词，逗号分隔")

    # 创建人
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    # 审批信息
    reviewed_by = Column(UUID(as_uuid=True), comment="审核人")
    approved_by = Column(UUID(as_uuid=True), comment="批准人")
    reviewed_at = Column(DateTime(timezone=True), comment="审核时间")
    approved_at = Column(DateTime(timezone=True), comment="批准时间")

    # 时效
    effective_date = Column(DateTime(timezone=True), comment="生效日期")
    review_date = Column(DateTime(timezone=True), comment="复审日期")
    expiry_date = Column(DateTime(timezone=True), comment="过期日期")

    is_deleted = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 关联
    category = relationship("DocumentCategory", back_populates="documents", lazy="joined")
    department = relationship("Department", back_populates="documents", lazy="joined")
    creator = relationship("User", back_populates="documents_created", lazy="joined")
    files = relationship(
        "DocumentFile",
        back_populates="document",
        order_by="DocumentFile.version_number.desc()",
        lazy="selectin",
    )
    approval_records = relationship(
        "ApprovalRecord",
        back_populates="document",
        order_by="ApprovalRecord.created_at.desc()",
        lazy="selectin",
    )


class DocumentFile(Base):
    """文件附件/版本文件"""
    __tablename__ = "document_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False, comment="版本号")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="存储路径")
    file_size = Column(BigInteger, default=0, comment="文件大小(bytes)")
    file_type = Column(String(50), comment="文件类型")
    change_summary = Column(Text, comment="变更说明")
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        comment="上传人",
    )
    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # 关联
    document = relationship("Document", back_populates="files")
