# 上传模块数据模型
# 使用项目现有的Image模型，不需要重复定义
from app.core.models import Image

# 为了保持API兼容性，创建别名
ImageUpload = Image