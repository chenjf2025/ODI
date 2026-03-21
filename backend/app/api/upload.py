import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from app.models.user import User
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

# 确保上传目录存在
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    通用文件上传接口 (支持 PDF 等格式)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")
    
    # 限制扩展名 (可配)
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png", "docx", "xlsx"]:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")
        
    # 生成唯一文件名并保存
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

    # 返回文件的静态路由 URL
    return {
        "success": True,
        "filename": file.filename,
        "url": f"/uploads/{unique_filename}"
    }
