"""文档管理路由 —— 质量体系文件的核心"""
import os
import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form, Query,
    status,
)
from sqlalchemy.orm import Session
from sqlalchemy import or_

from config import settings
from app.utils.database import get_db
from app.utils.auth import get_current_user, require_role
from app.utils.audit import log_audit
from app.models.document import Document, DocumentFile, DocumentStatus
from app.models.document_category import DocumentCategory
from app.models.department import Department
from app.models.user import User

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "txt", "zip", "rar", "jpg", "png",
}


def _save_file(upload: UploadFile, doc_id: str, version: int) -> DocumentFile:
    """保存上传文件并返回记录"""
    ext = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件类型: .{ext}")

    # 按日期分目录存储
    date_str = datetime.now().strftime("%Y/%m/%d")
    rel_dir = f"{date_str}/{doc_id}"
    abs_dir = os.path.join(settings.UPLOAD_DIR, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    # 生成唯一文件名
    unique_name = f"v{version}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = os.path.join(abs_dir, unique_name)

    content = upload.file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(400, f"文件超过大小限制 ({settings.MAX_UPLOAD_SIZE//1024//1024}MB)")

    with open(file_path, "wb") as f:
        f.write(content)

    return DocumentFile(
        document_id=doc_id,
        version_number=version,
        file_name=upload.filename,
        file_path=os.path.join(rel_dir, unique_name),
        file_size=len(content),
        file_type=ext,
    )


@router.get("")
def list_documents(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """文件列表（支持状态/分类/科室/关键词筛选 + 分页）"""
    query = db.query(Document).filter(Document.is_deleted == False)

    if status_filter:
        query = query.filter(Document.status == DocumentStatus(status_filter))
    if category_id:
        query = query.filter(Document.category_id == category_id)
    if department_id:
        query = query.filter(Document.department_id == department_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Document.title.ilike(like),
                Document.document_code.ilike(like),
                Document.keywords.ilike(like),
            )
        )

    total = query.count()
    docs = query.order_by(Document.updated_at.desc()) \
                .offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": str(d.id),
                "title": d.title,
                "document_code": d.document_code,
                "version": d.version,
                "status": d.status.value,
                "category": d.category.name if d.category else None,
                "department": d.department.name if d.department else None,
                "creator": d.creator.full_name if d.creator else None,
                "effective_date": d.effective_date.isoformat() if d.effective_date else None,
                "review_date": d.review_date.isoformat() if d.review_date else None,
                "expiry_date": d.expiry_date.isoformat() if d.expiry_date else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            }
            for d in docs
        ],
    }


@router.post("")
def create_document(
    title: str = Form(...),
    document_code: str = Form(...),
    category_id: str = Form(...),
    department_id: str = Form(None),
    description: str = Form(""),
    keywords: str = Form(""),
    effective_date: str = Form(None),
    review_date: str = Form(None),
    expiry_date: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新文件（支持首次上传附件）"""
    if db.query(Document).filter(Document.document_code == document_code).first():
        raise HTTPException(400, f"文件编号 {document_code} 已存在")

    def _parse_date(s):
        return datetime.fromisoformat(s) if s else None

    doc = Document(
        title=title,
        document_code=document_code,
        category_id=category_id,
        department_id=department_id,
        description=description,
        keywords=keywords,
        status=DocumentStatus.draft,
        created_by=current_user.id,
        effective_date=_parse_date(effective_date) if effective_date else None,
        review_date=_parse_date(review_date) if review_date else None,
        expiry_date=_parse_date(expiry_date) if expiry_date else None,
    )
    db.add(doc)
    db.flush()  # 获取 ID

    # 上传文件
    if file:
        doc_file = _save_file(file, str(doc.id), 1)
        doc_file.uploaded_by = current_user.id
        doc.files.append(doc_file)

    db.commit()
    db.refresh(doc)

    log_audit(db, current_user, "create_document", "document", str(doc.id),
              {"title": doc.title, "code": doc.document_code})

    return {"message": "创建成功", "id": str(doc.id)}


@router.get("/{doc_id}")
def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文件详情"""
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.is_deleted == False
    ).first()
    if not doc:
        raise HTTPException(404, "文件不存在")

    return {
        "id": str(doc.id),
        "title": doc.title,
        "document_code": doc.document_code,
        "category_id": str(doc.category_id) if doc.category_id else None,
        "category": doc.category.name if doc.category else None,
        "department_id": str(doc.department_id) if doc.department_id else None,
        "department": doc.department.name if doc.department else None,
        "version": doc.version,
        "status": doc.status.value,
        "description": doc.description,
        "keywords": doc.keywords,
        "creator": doc.creator.full_name if doc.creator else None,
        "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
        "review_date": doc.review_date.isoformat() if doc.review_date else None,
        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        "files": [
            {
                "id": str(f.id),
                "version_number": f.version_number,
                "file_name": f.file_name,
                "file_size": f.file_size,
                "change_summary": f.change_summary,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
            }
            for f in doc.files
        ],
        "approval_records": [
            {
                "id": str(a.id),
                "action": a.action.value,
                "comments": a.comments,
                "operator": a.operator.full_name if a.operator else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in doc.approval_records
        ],
    }


@router.put("/{doc_id}")
def update_document(
    doc_id: str,
    title: str = Form(None),
    description: str = Form(None),
    keywords: str = Form(None),
    category_id: str = Form(None),
    department_id: str = Form(None),
    effective_date: str = Form(None),
    review_date: str = Form(None),
    expiry_date: str = Form(None),
    file: UploadFile = File(None),
    change_summary: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新文件信息，可选上传新版本文件"""
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.is_deleted == False
    ).first()
    if not doc:
        raise HTTPException(404, "文件不存在")

    def _parse_date(s):
        return datetime.fromisoformat(s) if s else None

    if title is not None:
        doc.title = title
    if description is not None:
        doc.description = description
    if keywords is not None:
        doc.keywords = keywords
    if category_id is not None:
        doc.category_id = category_id
    if department_id is not None:
        doc.department_id = department_id
    if effective_date is not None:
        doc.effective_date = _parse_date(effective_date)
    if review_date is not None:
        doc.review_date = _parse_date(review_date)
    if expiry_date is not None:
        doc.expiry_date = _parse_date(expiry_date)

    # 上传新版本文件
    if file:
        new_version = doc.version + 1
        doc_file = _save_file(file, doc_id, new_version)
        doc_file.uploaded_by = current_user.id
        doc_file.change_summary = change_summary
        doc.files.append(doc_file)
        doc.version = new_version
        # 更新版本后状态回到起草
        doc.status = DocumentStatus.draft

    db.commit()

    log_audit(db, current_user, "update_document", "document", doc_id,
              {"title": doc.title, "version": doc.version})

    return {"message": "更新成功"}


@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """软删除文件"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文件不存在")
    doc.is_deleted = True
    db.commit()
    log_audit(db, current_user, "delete_document", "document", doc_id)
    return {"message": "删除成功"}
