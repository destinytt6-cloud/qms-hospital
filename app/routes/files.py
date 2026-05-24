"""文件下载路由"""
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config import settings
from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.models.document import DocumentFile
from app.models.user import User

router = APIRouter(prefix="/api/files", tags=["文件下载"])


@router.get("/{file_id}")
def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_file = db.query(DocumentFile).filter(DocumentFile.id == file_id).first()
    if not doc_file:
        raise HTTPException(404, "文件不存在")

    abs_path = os.path.join(settings.UPLOAD_DIR, doc_file.file_path)
    if not os.path.exists(abs_path):
        raise HTTPException(404, "文件已被物理删除")

    return FileResponse(
        path=abs_path,
        filename=doc_file.file_name,
        media_type="application/octet-stream",
    )
