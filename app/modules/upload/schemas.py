"""
上传模块的数据模型定义
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UploadResponse(BaseModel):
    """上传成功响应模型"""
    success: bool = True
    message: str
    image_id: int
    filename: str
    file_path: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime

class UploadErrorResponse(BaseModel):
    """上传错误响应模型"""
    success: bool = False
    message: str
    error_code: Optional[str] = None

class UploadStatusResponse(BaseModel):
    """上传状态查询响应模型"""
    success: bool
    message: str
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = None  # 0-100
    image_id: Optional[int] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
