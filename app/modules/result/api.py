"""
结果展示API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.result.schemas import (
    ResultListResponse, 
    ResultDetailResponse, 
    ResultRequest
)
from app.modules.result.services import (
    get_results_by_original_image,
    get_result_detail,
    get_user_results
)

router = APIRouter(prefix="/result", tags=["result"])

@router.get("/original/{original_image_id}", response_model=ResultListResponse)
async def get_results_for_original_image(
    original_image_id: int,
    db: Session = Depends(get_db)
):
    """
    获取原始图片对应的所有生成图片结果
    按评分从高到低排序
    """
    try:
        return get_results_by_original_image(db, original_image_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/generated/{generated_image_id}", response_model=ResultDetailResponse)
async def get_result_detail_api(
    generated_image_id: int,
    db: Session = Depends(get_db)
):
    """
    获取特定生成图片的详细结果信息
    包括评分、亮点、AI评价和拍摄指导
    """
    try:
        return get_result_detail(db, generated_image_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/user/{user_id}", response_model=list[ResultListResponse])
async def get_user_results(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=100, description="限制返回的原始图片数量"),
    db: Session = Depends(get_db)
):
    """
    获取用户的所有结果
    按原始图片分组，每个分组内的生成图片按评分从高到低排序
    """
    try:
        return get_user_results(db, user_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/health")
async def health_check():
    """结果模块健康检查"""
    return {"status": "healthy", "module": "result"}