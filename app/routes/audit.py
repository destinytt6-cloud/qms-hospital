"""审计日志查询路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.utils.auth import require_role
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter(prefix="/api/audit", tags=["审计日志"])


@router.get("")
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str = Query(None),
    target_type: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()) \
                .offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": str(log.id),
                "user": log.user.full_name if log.user else None,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
