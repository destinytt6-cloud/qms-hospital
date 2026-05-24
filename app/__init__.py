"""FastAPI 应用工厂"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.utils.database import init_db

# ─── 应用创建 ───

app = FastAPI(
    title="QMS 质量体系文件管理系统",
    description="医院/第三方检验实验室质量体系文件管理",
    version="1.0.0",
)

# CORS（局域网部署需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 模板
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ─── 注册路由 ───

from app.routes import auth, documents, departments, categories, approval, audit, files  # noqa

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(departments.router)
app.include_router(categories.router)
app.include_router(approval.router)
app.include_router(audit.router)
app.include_router(files.router)


# ─── 页面路由 ───

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/documents/new", response_class=HTMLResponse, include_in_schema=False)
def doc_new_page(request: Request):
    return templates.TemplateResponse("document_form.html", {"request": request, "mode": "create"})


@app.get("/documents/{doc_id}", response_class=HTMLResponse, include_in_schema=False)
def doc_detail_page(request: Request, doc_id: str):
    return templates.TemplateResponse("document_detail.html", {"request": request, "doc_id": doc_id})


@app.get("/documents/{doc_id}/edit", response_class=HTMLResponse, include_in_schema=False)
def doc_edit_page(request: Request, doc_id: str):
    return templates.TemplateResponse("document_form.html", {"request": request, "mode": "edit", "doc_id": doc_id})


@app.get("/admin/users", response_class=HTMLResponse, include_in_schema=False)
def admin_users(request: Request):
    return templates.TemplateResponse("admin_users.html", {"request": request})


@app.get("/admin/departments", response_class=HTMLResponse, include_in_schema=False)
def admin_departments(request: Request):
    return templates.TemplateResponse("admin_departments.html", {"request": request})


@app.get("/admin/categories", response_class=HTMLResponse, include_in_schema=False)
def admin_categories(request: Request):
    return templates.TemplateResponse("admin_categories.html", {"request": request})


@app.get("/admin/audit", response_class=HTMLResponse, include_in_schema=False)
def admin_audit(request: Request):
    return templates.TemplateResponse("admin_audit.html", {"request": request})


# ─── 启动事件 ───

@app.on_event("startup")
def on_startup():
    """初始化数据库表"""
    init_db()
