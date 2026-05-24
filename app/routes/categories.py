"""文件分类管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.utils.auth import require_role
from app.models.document_category import DocumentCategory
from app.models.user import User

router = APIRouter(prefix="/api/categories", tags=["文件分类"])


class CatCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    sort_order: int = 0

class CatUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None


@router.get("")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(DocumentCategory).order_by(DocumentCategory.sort_order).all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "code": c.code,
            "description": c.description,
            "sort_order": c.sort_order,
        }
        for c in cats
    ]


@router.post("")
def create_category(
    req: CatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if db.query(DocumentCategory).filter(DocumentCategory.code == req.code).first():
        raise HTTPException(status_code=400, detail="分类编号已存在")
    cat = DocumentCategory(
        name=req.name, code=req.code,
        description=req.description, sort_order=req.sort_order,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"message": "创建成功", "id": str(cat.id)}


@router.put("/{cat_id}")
def update_category(
    cat_id: str,
    req: CatUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    cat = db.query(DocumentCategory).filter(DocumentCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    if req.name is not None:
        cat.name = req.name
    if req.description is not None:
        cat.description = req.description
    if req.sort_order is not None:
        cat.sort_order = req.sort_order
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{cat_id}")
def delete_category(
    cat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    from app.models.document import Document
    if db.query(Document).filter(Document.category_id == cat_id).first():
        raise HTTPException(status_code=400, detail="该分类下还有文件，无法删除")
    cat = db.query(DocumentCategory).filter(DocumentCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(cat)
    db.commit()
    return {"message": "删除成功"}
