"""认证与用户管理路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.utils.auth import create_access_token, get_current_user, require_role
from app.utils.audit import log_audit
from app.models.user import User
from app.models.department import Department

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ─── 请求/响应模型 ───

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str | None = None
    role: str = "user"
    department_id: str | None = None

class UserUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    role: str | None = None
    department_id: str | None = None
    is_active: bool | None = None


# ─── 路由 ───

@router.post("/login", summary="用户登录")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not user.verify_password(req.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    token = create_access_token({"sub": str(user.id)})
    log_audit(db, user, "login", "user", str(user.id), {"username": user.username})

    return TokenResponse(
        access_token=token,
        user={
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department.name if user.department else None,
        },
    )


@router.get("/me", summary="当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "department": current_user.department.name if current_user.department else None,
        "is_active": current_user.is_active,
    }


@router.get("/users", summary="用户列表")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": str(u.id),
            "username": u.username,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "department": u.department.name if u.department else None,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.post("/users", summary="创建用户")
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=req.username,
        full_name=req.full_name,
        email=req.email,
        role=req.role,
        department_id=req.department_id,
    )
    user.set_password(req.password)
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(db, current_user, "create_user", "user", str(user.id))

    return {"message": "创建成功", "id": str(user.id)}


@router.put("/users/{user_id}", summary="更新用户")
def update_user(
    user_id: str,
    req: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.full_name is not None:
        user.full_name = req.full_name
    if req.email is not None:
        user.email = req.email
    if req.role is not None:
        user.role = req.role
    if req.department_id is not None:
        user.department_id = req.department_id
    if req.is_active is not None:
        user.is_active = req.is_active

    db.commit()
    return {"message": "更新成功"}
