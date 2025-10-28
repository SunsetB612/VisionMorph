"""
生成API
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.models import User
from app.modules.generate.services import (
    create_generation, 
    create_generation_with_progress,
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

@router.post("/generate/stream")
async def create_generation_stream(
    request: GenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建生成任务（SSE 流式接口，实时推送进度）"""
    
    async def event_generator():
        """SSE 事件生成器"""
        try:
            # 调用生成器版本的服务函数
            for progress in create_generation_with_progress(db, request):
                # 格式化为 SSE 格式：data: {json}\n\n
                yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"
        except Exception as e:
            # 发送错误消息
            error_msg = {
                "status": "failed",
                "current": 0,
                "total": 0,
                "message": f"生成失败: {str(e)}"
            }
            yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲（如果使用了 Nginx）
        }
    )