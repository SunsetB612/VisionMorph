"""
结果展示模块数据模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ResultImageInfo(BaseModel):
    """结果图片信息"""
    generated_image_id: int
    result_image_id: int
    filename: str
    file_path: str
    overall_score: int = Field(..., ge=1, le=100, description="总体评分1-100")
    highlights: Optional[str] = None
    created_at: datetime

class ResultDetailInfo(BaseModel):
    """结果详细信息"""
    generated_image_id: int
    result_image_id: int
    filename: str
    file_path: str
    overall_score: int = Field(..., ge=1, le=100, description="总体评分1-100")
    highlights: Optional[str] = None
    ai_comment: Optional[str] = None
    shooting_guidance: Optional[str] = None
    created_at: datetime

class ResultListResponse(BaseModel):
    """结果列表响应"""
    original_image_id: int
    total_count: int
    results: List[ResultImageInfo]

class ResultDetailResponse(BaseModel):
    """结果详情响应"""
    result: ResultDetailInfo

class ResultRequest(BaseModel):
    """结果请求"""
    original_image_id: int = Field(..., description="原始图片ID")