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

class GenerationProgressUpdate(BaseModel):
    """SSE 进度更新"""
    status: str  # started/generating/completed/failed
    current: int  # 当前已完成数量
    total: int  # 总数量
    message: str  # 提示信息