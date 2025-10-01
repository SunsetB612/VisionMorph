"""
生成模块数据模式
"""
from pydantic import BaseModel
from datetime import datetime

class GenerationRequest(BaseModel):
    """生成请求"""
    original_image_id: int

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