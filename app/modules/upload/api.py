from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.modules.upload.services import UploadService
from app.modules.upload.schemas import UploadResponse, UploadStatusResponse
from app.core.security import get_current_active_user
from app.core.models import User

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """上传图片接口"""
    return await UploadService.upload_image(file, current_user.id)

@router.get("/upload/status/{file_id}", response_model=UploadStatusResponse)
async def get_upload_status(file_id: str):
    """获取上传状态"""
    return UploadService.get_upload_status(file_id)