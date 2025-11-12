"""
裁剪模块数据模式
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CropRequest(BaseModel):
    """裁剪任务请求"""

    original_image_id: int = Field(..., description="原始图片ID")
    top_n: int = Field(
        3,
        ge=1,
        le=10,
        description="需要返回的裁剪图片数量",
    )
    method: Optional[str] = Field(
        default=None,
        description="显著性检测方法，可选值：frequency_tuned、srm，默认自动选择",
    )
    use_generated_images: bool = Field(
        default=True,
        description="是否基于 generate 模块生成的图片执行裁剪",
    )


class CropResponse(BaseModel):
    """裁剪任务响应"""

    original_image_id: int
    cropped_count: int
    message: str


class CroppedImageInfo(BaseModel):
    """裁剪图片信息"""

    id: int
    temp_image_id: int
    filename: str
    file_path: str
    created_at: datetime


class CropListResponse(BaseModel):
    """裁剪图片列表"""

    original_image_id: int
    total_count: int
    crops: List[CroppedImageInfo]

