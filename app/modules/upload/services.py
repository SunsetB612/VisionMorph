import os
import uuid
import hashlib
import time
from io import BytesIO
from fastapi import UploadFile, HTTPException
from PIL import Image as PILImage
from app.core.database import get_db
from app.core.models import Image
from app.modules.upload.schemas import UploadResponse, UploadErrorResponse, UploadStatusResponse

# 配置
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
BASE_STATIC_DIR = "static"  # 基础静态文件目录

class UploadService:
    """上传服务类"""
    
    @staticmethod
    def get_user_directory_structure(user_id: int) -> dict:
        """获取用户目录结构"""
        user_dir = os.path.join(BASE_STATIC_DIR, f"user{user_id}")
        return {
            "user_dir": user_dir,
            "avatar_dir": os.path.join(user_dir, "avatar"),
            "original_dir": os.path.join(user_dir, "original"),
            "temp_dir": os.path.join(user_dir, "temp"),
            "results_dir": os.path.join(user_dir, "results")
        }
    
    @staticmethod
    def create_user_directories(user_id: int) -> dict:
        """为用户创建完整的目录结构"""
        dirs = UploadService.get_user_directory_structure(user_id)
        
        # 创建所有目录
        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        return dirs
    
    @staticmethod
    def get_or_create_default_user():
        """获取或创建默认用户"""
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
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
        finally:
            session.close()
    
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
    def generate_user_filename(user_id: int, original_filename: str) -> tuple[str, str]:
        """生成用户友好的文件名"""
        # 获取文件扩展名
        ext = os.path.splitext(original_filename)[1].lower()
        
        # 获取用户已上传的图片数量
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            result = session.execute(text("""
                SELECT COUNT(*) FROM images WHERE user_id = :user_id
            """), {'user_id': user_id})
            count = result.fetchone()[0] or 0
        finally:
            session.close()
        
        # 生成新的文件名：user{id}_img_{序号}_{时间戳}{扩展名}
        timestamp = int(time.time() * 1000)
        sequence = count + 1
        filename = f"user{user_id}_img_{sequence:03d}_{timestamp}{ext}"
        
        return filename, str(sequence)
    
    @staticmethod
    async def save_uploaded_file(file: UploadFile, user_id: int) -> tuple[str, str, str]:
        """保存上传的文件并返回文件ID、路径和文件名"""
        # 创建用户目录结构
        dirs = UploadService.create_user_directories(user_id)
        
        # 生成用户友好的文件名
        filename, sequence = UploadService.generate_user_filename(user_id, file.filename)
        file_path = os.path.join(dirs["original_dir"], filename)
        
        # 读取文件内容
        content = await file.read()
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        return sequence, file_path, filename
    
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
            sequence, file_path, filename = await UploadService.save_uploaded_file(file, user_id)
            
            # 保存到数据库
            from app.core.database import SessionLocal
            from sqlalchemy import text
            
            session = SessionLocal()
            try:
                # 使用原生SQL插入数据
                result = session.execute(text("""
                    INSERT INTO images (user_id, filename, original_filename, file_path, file_size, mime_type, width, height)
                    VALUES (:user_id, :filename, :original_filename, :file_path, :file_size, :mime_type, :width, :height)
                """), {
                    'user_id': user_id,
                    'filename': filename,
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
                """), {'filename': filename})
                
                record = result.fetchone()
                if not record:
                    raise HTTPException(status_code=500, detail="数据库记录创建失败")
                
                image_id = record[0]
                created_at = record[1]
            finally:
                session.close()
            
            return UploadResponse(
                success=True,
                message="图片上传成功",
                image_id=image_id,
                filename=filename,
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
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
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
        finally:
            session.close()