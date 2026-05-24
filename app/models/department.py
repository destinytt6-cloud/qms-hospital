"""科室/部门模型"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.utils.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="科室名称")
    code = Column(String(50), unique=True, nullable=False, comment="科室编号")
    description = Column(Text, comment="描述")
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
    users = relationship("User", back_populates="department")
    documents = relationship("Document", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"
