from fastapi import APIRouter, UploadFile, File, HTTPException
from app.modules.upload.services import UploadService
from app.modules.upload.schemas import UploadResponse, UploadStatusResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """上传图片接口"""
    return await UploadService.upload_image(file)

@router.get("/upload/status/{file_id}", response_model=UploadStatusResponse)
async def get_upload_status(file_id: str):
    """获取上传状态"""
    return UploadService.get_upload_status(file_id)