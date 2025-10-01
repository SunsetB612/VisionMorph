"""
打分API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.score.schemas import (
    ScoreRequest, 
    ScoreResponse, 
    ScoreInfo, 
    GeneratedImageScore
)
from app.modules.score.services import (
    create_scores,
    get_scores_by_original_image,
    get_score_details
)

router = APIRouter(prefix="/score", tags=["score"])

@router.post("/create", response_model=ScoreResponse)
async def create_image_scores(
    request: ScoreRequest,
    db: Session = Depends(get_db)
):
    """
    为原始图片对应的所有生成图片创建评分
    """
    try:
        return create_scores(db, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/original/{original_image_id}", response_model=list[GeneratedImageScore])
async def get_scores_for_original_image(
    original_image_id: int,
    db: Session = Depends(get_db)
):
    """
    获取原始图片对应的所有生成图片的评分
    """
    try:
        return get_scores_by_original_image(db, original_image_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/generated/{generated_image_id}", response_model=ScoreInfo)
async def get_score_detail(
    generated_image_id: int,
    db: Session = Depends(get_db)
):
    """
    获取特定生成图片的详细评分信息
    """
    try:
        return get_score_details(db, generated_image_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")
