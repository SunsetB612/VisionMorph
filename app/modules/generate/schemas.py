"""
生成模块数据模式
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class GenerationRequest(BaseModel):
    """生成请求"""
    original_image_id: int
    view_angles: Optional[List[str]] = None  # 视角大方向列表，可选

class GenerationResponse(BaseModel):
    """生成响应"""
    original_image_id: int
    generated_count: int
    message: str

class GeneratedImageInfo(BaseModel):
    """生成图片信息"""
    id: int
    filename: str
    file_path: str
    created_at: datetime