"""
结果展示API路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.models import User
from app.modules.result.schemas import (
    ResultListResponse,
    ResultDetailResponse,
    StaticResultResponse,
    ShowcaseEvolutionResponse,
)
from app.modules.result.services import (
    get_results_by_original_image,
    get_result_detail,
    get_user_results,
    get_static_output_results,
    get_showcase_evolution,
)

router = APIRouter(prefix="/result", tags=["result"])

@router.get("/original/{original_image_id}", response_model=ResultListResponse)
async def get_results_for_original_image(
    original_image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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

@router.get("/static/showcase", response_model=ShowcaseEvolutionResponse)
async def get_static_showcase_api():
    """
    构图进化论：input/1、2、3 与各自 output 目录中评分最高的一张 AI 结果对比数据。
    """
    try:
        return get_showcase_evolution()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法获取展示数据: {str(e)}")


@router.get("/static", response_model=StaticResultResponse)
async def get_static_results_api(
    input_key: Optional[str] = Query(
        default=None,
        description="输入示例编号，例如 '1'、'2' 或 '3'"
    )
):
    """
    获取固定输出目录中的所有图片结果，按评分排序
    """
    try:
        return get_static_output_results(input_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法获取固定结果: {str(e)}")

@router.get("/user/{user_id}", response_model=list[ResultListResponse])
async def get_user_results(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=100, description="限制返回的原始图片数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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