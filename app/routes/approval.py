"""审批流程路由（提交审核、批准、驳回、发布、归档、撤回）"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.utils.audit import log_audit
from app.models.document import Document, DocumentStatus
from app.models.approval import ApprovalRecord, ApprovalAction
from app.models.user import User

router = APIRouter(prefix="/api/approval", tags=["审批流程"])


class ApprovalRequest(BaseModel):
    comments: str = ""


def _record_action(
    db: Session,
    document: Document,
    action: ApprovalAction,
    user: User,
    comments: str,
    new_status: DocumentStatus,
):
    """记录审批操作并更新文件状态"""
    record = ApprovalRecord(
        document_id=document.id,
        action=action,
        comments=comments,
        operator_id=user.id,
    )
    document.status = new_status
    db.add(record)
    db.commit()


@router.post("/{doc_id}/submit", summary="提交审核")
def submit_for_review(
    doc_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """起草 → 审核中"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文件不存在")
    if doc.status != DocumentStatus.draft:
        raise HTTPException(400, f"当前状态 ({doc.status.value}) 不可提交审核")

    _record_action(db, doc, ApprovalAction.submit, current_user,
                   req.comments, DocumentStatus.review)
    log_audit(db, current_user, "submit_document", "document", doc_id)
    return {"message": "已提交审核"}


@router.post("/{doc_id}/approve", summary="批准")
def approve_document(
    doc_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审核中 → 已批准"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文件不存在")
    if doc.status != DocumentStatus.review:
        raise HTTPException(400, f"当前状态 ({doc.status.value}) 不可批准")
    if current_user.role not in ("admin", "reviewer"):
        raise HTTPException(403, "仅有管理员和审核员可以批准")

    _record_action(db, doc, ApprovalAction.approve, current_user,
                   req.comments, DocumentStatus.approved)
    log_audit(db, current_user, "approve_document", "document", doc_id)
    return {"message": "已批准"}


@router.post("/{doc_id}/reject", summary="驳回")
def reject_document(
    doc_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """退回起草状态"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文件不存在")
    if doc.status not in (DocumentStatus.review, DocumentStatus.approved):
        raise HTTPException(400, "当前状态不可驳回")

    if not req.comments:
        raise HTTPException(400, "驳回必须填写意见")

    _record_action(db, doc, ApprovalAction.reject, current_user,
                   req.comments, DocumentStatus.draft)
    log_audit(db, current_user, "reject_document", "document", doc_id)
    return {"message": "已驳回"}


@router.post("/{doc_id}/publish", summary="发布")
def publish_document(
    doc_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """已批准 → 已发布"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文件不存在")
    if doc.status != DocumentStatus.approved:
        raise HTTPException(400, "仅已批准的文件可以发布")
    if current_user.role not in ("admin", "reviewer"):
        raise HTTPException(403, "仅有管理员和审核员可以发布")

    _record_action(db, doc, ApprovalAction.publish, current_user,
                   req.comments, DocumentStatus.published)
    log_audit(db, current_user, "publish_document", "document", doc_id)
    return {"message": "已发布"}


@router.post("/{doc_id}/archive", summary="归档")
def archive_document(
    doc_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """已发布 → 已归档"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文件不存在")
    if doc.status != DocumentStatus.published:
        raise HTTPException(400, "仅已发布的文件可以归档")

    _record_action(db, doc, ApprovalAction.archive, current_user,
                   req.comments, DocumentStatus.archived)
    log_audit(db, current_user, "archive_document", "document", doc_id)
    return {"message": "已归档"}
