"""审计日志写入工具"""
import json
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.utils.auth import get_current_user


def log_audit(
    db: Session,
    user: User,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    """写入审计日志"""
    log = AuditLog(
        user_id=user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details, ensure_ascii=False) if details else None,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
