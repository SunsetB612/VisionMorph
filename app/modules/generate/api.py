"""
生成API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.models import User
from app.modules.generate.services import (
    create_generation, 
    get_generated_images
)
from app.modules.generate.schemas import GenerationRequest, GenerationResponse, GeneratedImageInfo

router = APIRouter()

@router.post("/generate", response_model=GenerationResponse)
def create_generation_task(
    request: GenerationRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建生成任务"""
    try:
        return create_generation(db, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/generate/images/{original_image_id}", response_model=List[GeneratedImageInfo])
def get_generated_images_list(
    original_image_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取生成图片列表"""
    return get_generated_images(db, original_image_id)