"""
结果展示模块数据模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ResultImageInfo(BaseModel):
    """结果图片信息"""
    generated_image_id: int
    filename: str
    file_path: str
    overall_score: int = Field(..., ge=1, le=100, description="总体评分1-100")
    highlights: Optional[str] = None
    created_at: datetime

class ResultDetailInfo(BaseModel):
    """结果详细信息"""
    generated_image_id: int
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

class StaticImageResult(BaseModel):
    """固定输出目录中的图片结果"""
    id: str
    group: str
    image_name: str
    filename: str
    relative_path: str
    overall_score: float
    shooting_guidance: Optional[str] = None
    viewpoint_feature: Optional[str] = Field(
        default=None,
        description="一句话概括优势特征（Excel 列）",
    )
    composition_highlights: Optional[str] = Field(
        default=None,
        description="推荐视角优点（Excel 列）",
    )
    operation_guide: Optional[str] = Field(
        default=None,
        description="操作指南（Excel 列）",
    )
    orientation: Optional[str] = None
    crop_type: Optional[str] = None

class StaticResultResponse(BaseModel):
    """固定输出目录结果列表"""
    total_count: int
    results: List[StaticImageResult]


class ShowcaseEvolutionItem(BaseModel):
    """首页「构图进化论」单条：原图 + 该示例下评分最高的 AI 图"""
    input_key: str
    original_relative_path: Optional[str] = Field(
        default=None,
        description="原图 URL 路径，如 /input/1.jpg",
    )
    best_result: Optional[StaticImageResult] = None


class ShowcaseEvolutionResponse(BaseModel):
    items: List[ShowcaseEvolutionItem]

class ResultRequest(BaseModel):
    """结果请求"""
    original_image_id: int = Field(..., description="原始图片ID")