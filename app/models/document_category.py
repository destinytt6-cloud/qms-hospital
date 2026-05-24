"""文件分类模型（质量手册、程序文件、作业指导书、记录表格等）"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.utils.database import Base


class DocumentCategory(Base):
    __tablename__ = "document_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="分类名称")
    code = Column(String(50), unique=True, nullable=False, comment="分类编号")
    description = Column(Text, comment="描述")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # 关联
    documents = relationship("Document", back_populates="category")

    def __repr__(self):
        return f"<DocumentCategory {self.name}>"
