"""
数据库模型定义
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """用户模型"""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    avatar_path: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Image:
    """图片模型"""
    id: Optional[int] = None
    user_id: int = 0
    filename: str = ""
    original_filename: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: Optional[datetime] = None

@dataclass
class GeneratedImage:
    """生成效果图模型"""
    id: Optional[int] = None
    original_image_id: int = 0
    filename: str = ""
    file_path: str = ""
    created_at: Optional[datetime] = None

@dataclass
class ImageEvaluation:
    """图片评价模型"""
    id: Optional[int] = None
    generated_image_id: int = 0
    overall_score: Optional[int] = None  # 1-100
    highlights: Optional[str] = None
    ai_comment: Optional[str] = None
    shooting_guidance: Optional[str] = None
    created_at: Optional[datetime] = None
