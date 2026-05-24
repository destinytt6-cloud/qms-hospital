"""用户模型"""
import uuid
from datetime import datetime, timezone

import bcrypt

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.utils.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, comment="登录账号")
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(50), nullable=False, comment="姓名")
    email = Column(String(100), comment="邮箱")
    role = Column(
        String(20),
        nullable=False,
        default="user",
        comment="角色: admin/reviewer/user",
    )
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id"),
        comment="所属科室ID",
    )
    is_active = Column(Boolean, default=True)
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
    department = relationship("Department", back_populates="users", lazy="joined")
    documents_created = relationship(
        "Document", back_populates="creator", foreign_keys="Document.created_by"
    )

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def __repr__(self):
        return f"<User {self.username}>"
