"""
打分模块数据模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ScoreRequest(BaseModel):
    """打分请求"""
    original_image_id: int = Field(..., description="原始图片ID")

class ScoreResponse(BaseModel):
    """打分响应"""
    original_image_id: int
    scored_count: int
    message: str

class ScoreInfo(BaseModel):
    """评分信息"""
    id: int
    generated_image_id: int
    overall_score: int = Field(..., ge=1, le=100, description="总体评分1-100")
    highlights: Optional[str] = None
    ai_comment: Optional[str] = None
    shooting_guidance: Optional[str] = None
    created_at: datetime

class GeneratedImageScore(BaseModel):
    """生成图片评分信息"""
    generated_image_id: int
    filename: str
    file_path: str
    overall_score: int
    created_at: datetime
