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
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}  # 支持上传的格式
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
BASE_STATIC_DIR = "static"  # 基础静态文件目录

# 注意：虽然支持多种格式上传，但所有图片都会统一转换为JPG格式存储

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
            "results_dir": os.path.join(user_dir, "results"),
            "excel_dir": os.path.join(user_dir, "excel"),
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
    def resize_to_64_multiple(image: PILImage.Image, max_size: int = 1024) -> PILImage.Image:
        """
        缩放图片到64的倍数（Qwen模型要求）
        
        Args:
            image: PIL图片对象
            max_size: 最大尺寸（长边不超过此值）
            
        Returns:
            处理后的PIL图片对象
        """
        width, height = image.size
        print(f"📏 原图尺寸: {width}x{height}")
        
        # 计算缩放比例（如果长边超过max_size）
        scale = min(max_size / width, max_size / height, 1.0)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # 对齐到64的倍数（向下取整）
        new_width = (new_width // 64) * 64
        new_height = (new_height // 64) * 64
        
        # 确保至少是64x64
        new_width = max(new_width, 64)
        new_height = max(new_height, 64)
        
        # 如果尺寸发生变化，进行缩放
        if (new_width, new_height) != (width, height):
            # 使用LANCZOS高质量缩放算法
            image = image.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
            print(f"📐 已缩放到模型兼容尺寸: {new_width}x{new_height}")
        else:
            print(f"✅ 原图尺寸已符合要求，无需缩放")
        
        return image
    
    @staticmethod
    def generate_user_filename(user_id: int, original_filename: str) -> tuple[str, str]:
        """生成用户友好的文件名"""
        # 统一使用.jpg扩展名（所有图片都会转换为jpg格式）
        ext = ".jpg"
        
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
        
        # 生成新的文件名：user{id}_img_{序号}_{时间戳}.jpg
        timestamp = int(time.time() * 1000)
        sequence = count + 1
        filename = f"user{user_id}_img_{sequence:03d}_{timestamp}{ext}"
        
        return filename, str(sequence)
    
    @staticmethod
    async def save_uploaded_file(file: UploadFile, user_id: int) -> tuple[str, str, str]:
        """保存上传的文件并返回文件ID、路径和文件名（统一转换为jpg格式）"""
        # 创建用户目录结构
        dirs = UploadService.create_user_directories(user_id)
        
        # 生成用户友好的文件名（统一使用.jpg扩展名）
        filename, sequence = UploadService.generate_user_filename(user_id, file.filename)
        file_path = os.path.join(dirs["original_dir"], filename)
        
        # 读取文件内容
        content = await file.read()
        
        # 使用PIL打开图片并转换为jpg格式
        try:
            image = PILImage.open(BytesIO(content))
            
            # 如果图片是RGBA模式（如PNG），转换为RGB模式
            if image.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = PILImage.new('RGB', image.size, (255, 255, 255))
                # 如果有透明通道，使用alpha通道进行合成
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[3])  # 使用alpha通道作为mask
                elif image.mode == 'P' and 'transparency' in image.info:
                    image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background
                print("📷 已将4通道图片转为3通道RGB（白色背景）")
            elif image.mode != 'RGB':
                # 其他模式直接转换为RGB
                image = image.convert('RGB')
                print(f"📷 已将{image.mode}模式转为RGB")
            
            # 缩放到64的倍数（Qwen模型要求）
            image = UploadService.resize_to_64_multiple(image, max_size=1024)
            
            # 保存为jpg格式，设置高质量
            image.save(file_path, 'JPEG', quality=95, optimize=True)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"图片格式转换失败: {str(e)}")
        
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
            
            # 重置文件指针
            await file.seek(0)
            
            # 保存文件（会转换为jpg格式并缩放到64倍数）
            sequence, file_path, filename = await UploadService.save_uploaded_file(file, user_id)
            
            # 获取转换后的文件大小和尺寸（从保存后的文件获取）
            converted_file_size = os.path.getsize(file_path)
            
            # 获取处理后的图片尺寸
            with PILImage.open(file_path) as img:
                width, height = img.size
            
            # 保存到数据库
            from app.core.database import SessionLocal
            from sqlalchemy import text
            
            session = SessionLocal()
            try:
                # 使用原生SQL插入数据（统一保存为jpg格式）
                result = session.execute(text("""
                    INSERT INTO images (user_id, filename, original_filename, file_path, file_size, mime_type, width, height)
                    VALUES (:user_id, :filename, :original_filename, :file_path, :file_size, :mime_type, :width, :height)
                """), {
                    'user_id': user_id,
                    'filename': filename,
                    'original_filename': file.filename,
                    'file_path': file_path,
                    'file_size': converted_file_size,  # 使用转换后的文件大小
                    'mime_type': "image/jpeg",  # 统一为JPEG格式
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
                message=f"图片上传成功（已转换为JPG格式，尺寸：{width}x{height}）",
                image_id=image_id,
                filename=filename,
                file_path=file_path,
                file_size=converted_file_size,
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