import os
import uuid
import hashlib
from io import BytesIO
from fastapi import UploadFile, HTTPException
from PIL import Image as PILImage
from app.core.database import get_db
from app.core.models import Image
from app.modules.upload.schemas import UploadResponse, UploadErrorResponse, UploadStatusResponse

# 配置
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = "static/original"  # 使用项目设计的存储路径

class UploadService:
    """上传服务类"""
    
    @staticmethod
    def get_or_create_default_user():
        """获取或创建默认用户"""
        with get_db() as session:
            from sqlalchemy import text
            
            # 首先尝试获取默认用户
            result = session.execute(text("SELECT id FROM users WHERE username = 'admin'"))
            user = result.fetchone()
            
            if user:
                return user[0]
            
            # 如果没有默认用户，创建一个
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            result = session.execute(text("""
                INSERT INTO users (username, email, password_hash) 
                VALUES ('admin', 'admin@visionmorph.com', :password_hash)
            """), {'password_hash': password_hash})
            
            session.commit()
            return result.lastrowid
    
    @staticmethod
    def validate_image(file: UploadFile) -> bool:
        """验证图片文件"""
        if not file.filename:
            return False
        
        # 检查文件扩展名
        ext = os.path.splitext(file.filename)[1].lower()
        return ext in ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_image_dimensions(content: bytes) -> tuple[int, int]:
        """获取图片的宽度和高度"""
        try:
            # 使用PIL打开图片
            image = PILImage.open(BytesIO(content))
            return image.size  # 返回 (width, height)
        except Exception as e:
            # 如果无法获取尺寸，返回默认值
            print(f"⚠️ 无法获取图片尺寸: {e}")
            return (0, 0)
    
    @staticmethod
    async def save_uploaded_file(file: UploadFile) -> tuple[str, str]:
        """保存上传的文件并返回文件ID和路径"""
        # 创建存储目录
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{file_id}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 读取文件内容
        content = await file.read()
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        return file_id, file_path
    
    @staticmethod
    async def upload_image(file: UploadFile, user_id: int = None) -> UploadResponse:
        """处理图片上传"""
        try:
            # 如果没有提供用户ID，获取或创建默认用户
            if user_id is None:
                user_id = UploadService.get_or_create_default_user()
            # 验证文件
            if not UploadService.validate_image(file):
                raise HTTPException(
                    status_code=400, 
                    detail="不支持的文件格式，请上传 JPG、PNG 或 WebP 格式的图片"
                )
            
            # 检查文件大小
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail="文件过大，请上传小于10MB的图片"
                )
            
            # 获取图片尺寸
            width, height = UploadService.get_image_dimensions(content)
            
            # 重置文件指针
            await file.seek(0)
            
            # 保存文件
            file_id, file_path = await UploadService.save_uploaded_file(file)
            
            # 保存到数据库
            with get_db() as session:
                from sqlalchemy import text
                
                # 使用原生SQL插入数据
                result = session.execute(text("""
                    INSERT INTO images (user_id, filename, original_filename, file_path, file_size, mime_type, width, height)
                    VALUES (:user_id, :filename, :original_filename, :file_path, :file_size, :mime_type, :width, :height)
                """), {
                    'user_id': user_id,
                    'filename': f"{file_id}{os.path.splitext(file.filename)[1].lower()}",
                    'original_filename': file.filename,
                    'file_path': file_path,
                    'file_size': len(content),
                    'mime_type': file.content_type or "image/jpeg",
                    'width': width,
                    'height': height
                })
                
                session.commit()
                
                # 获取插入的记录ID
                result = session.execute(text("""
                    SELECT id, created_at FROM images 
                    WHERE filename = :filename
                """), {'filename': f"{file_id}{os.path.splitext(file.filename)[1].lower()}"})
                
                record = result.fetchone()
                if not record:
                    raise HTTPException(status_code=500, detail="数据库记录创建失败")
                
                image_id = record[0]
                created_at = record[1]
            
            return UploadResponse(
                success=True,
                message="图片上传成功",
                image_id=image_id,
                filename=f"{file_id}{os.path.splitext(file.filename)[1].lower()}",
                file_path=file_path,
                file_size=len(content),
                created_at=created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
    
    @staticmethod
    def get_upload_status(file_id: str) -> UploadStatusResponse:
        """获取上传状态"""
        with get_db() as session:
            from sqlalchemy import text
            
            # 查找匹配的图片记录
            result = session.execute(text("""
                SELECT id, filename, file_path, file_size, created_at FROM images 
                WHERE filename LIKE :file_id_pattern
            """), {'file_id_pattern': f"{file_id}%"})
            
            record = result.fetchone()
            
            if not record:
                return UploadStatusResponse(
                    success=False,
                    message="未找到指定的上传记录",
                    status="not_found"
                )
            
            return UploadStatusResponse(
                success=True,
                message="上传记录查询成功",
                status="uploaded",
                image_id=record[0],
                filename=record[1],
                file_path=record[2]
            )