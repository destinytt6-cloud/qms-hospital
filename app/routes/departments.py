"""科室管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.utils.auth import require_role
from app.models.department import Department
from app.models.user import User

router = APIRouter(prefix="/api/departments", tags=["科室管理"])


class DeptCreate(BaseModel):
    name: str
    code: str
    description: str | None = None

class DeptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


@router.get("")
def list_departments(db: Session = Depends(get_db)):
    depts = db.query(Department).order_by(Department.code).all()
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "code": d.code,
            "description": d.description,
        }
        for d in depts
    ]


@router.post("")
def create_department(
    req: DeptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if db.query(Department).filter(Department.code == req.code).first():
        raise HTTPException(status_code=400, detail="科室编号已存在")

    dept = Department(name=req.name, code=req.code, description=req.description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return {"message": "创建成功", "id": str(dept.id)}


@router.put("/{dept_id}")
def update_department(
    dept_id: str,
    req: DeptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="科室不存在")

    if req.name is not None:
        dept.name = req.name
    if req.description is not None:
        dept.description = req.description
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{dept_id}")
def delete_department(
    dept_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="科室不存在")
    db.delete(dept)
    db.commit()
    return {"message": "删除成功"}
