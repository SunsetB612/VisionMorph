"""
裁剪模块 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import User
from app.core.security import get_current_active_user
from app.modules.crop.schemas import CropListResponse, CropRequest, CropResponse
from app.modules.crop.services import create_crop_task, get_crops_by_original_image

router = APIRouter()


@router.post("/crop", response_model=CropResponse)
def create_crop(
    request: CropRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    触发裁剪任务。
    """
    try:
        return create_crop_task(db, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/crop/{original_image_id}", response_model=CropListResponse)
def list_crops(
    original_image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取指定原始图片的裁剪结果。
    """
    return get_crops_by_original_image(db, original_image_id)


