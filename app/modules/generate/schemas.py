"""
生成模块数据模式
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class GenerationRequest(BaseModel):
    """生成请求"""
    original_image_id: int
    view_angles: Optional[List[str]] = None

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
    view_angles: Optional[str] = None
    prompt_file_path: Optional[str] = None
    prompt_content: Optional[str] = None  # 读取的prompt文本内容
    created_at: datetime