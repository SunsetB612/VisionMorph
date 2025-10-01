"""
生成服务
"""
import os
import shutil
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
# 生成服务 - 处理图片生成逻辑
from app.modules.generate.schemas import GenerationRequest, GenerationResponse, GeneratedImageInfo

def create_generation(db: Session, request: GenerationRequest) -> GenerationResponse:
    """创建生成任务"""
    
    try:
        # 获取原始图片信息和用户ID
        result = db.execute(text("""
            SELECT i.id, i.filename, i.file_path, i.user_id, u.username 
            FROM images i 
            JOIN users u ON i.user_id = u.id 
            WHERE i.id = :image_id
        """), {"image_id": request.original_image_id}).fetchone()
        
        if not result:
            raise ValueError("原始图片不存在")
        
        original_file_path = result[2]
        user_id = result[3]
        username = result[4]
        
        if not os.path.exists(original_file_path):
            raise ValueError(f"原始图片文件不存在: {original_file_path}")
        
        # 创建用户目录结构
        from app.modules.upload.services import UploadService
        dirs = UploadService.create_user_directories(user_id)
        results_dir = dirs["results_dir"]
        
        generated_count = 0
        
        # 生成唯一的时间戳前缀
        import time
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        
        # 获取该用户已生成的图片数量，用于序号
        existing_count = db.execute(text("""
            SELECT COUNT(*) FROM generated_images gi
            JOIN images i ON gi.original_image_id = i.id
            WHERE i.user_id = :user_id
        """), {"user_id": user_id}).fetchone()[0]
        
        for i in range(1, 11):
            try:
                # 文件命名规则：user{user_id}_img_{序号}_{时间戳}_generated_{i}.jpg
                image_sequence = existing_count + i
                new_filename = f"user{user_id}_img_{image_sequence:03d}_{timestamp}_generated_{i}.jpg"
                new_file_path = os.path.join(results_dir, new_filename)
                
                shutil.copy2(original_file_path, new_file_path)
                
                db.execute(text("""
                    INSERT INTO generated_images (original_image_id, filename, file_path, created_at)
                    VALUES (:original_image_id, :filename, :file_path, NOW())
                """), {
                    "original_image_id": result[0],
                    "filename": new_filename,
                    "file_path": new_file_path
                })
                generated_count += 1
                
            except Exception as e:
                print(f"生成第{i}张图片失败: {e}")
                continue
        
        if generated_count == 0:
            raise ValueError("没有成功生成任何图片")
        
        db.commit()
        
        # 自动为刚生成的图片进行评分
        try:
            from app.modules.score.services import create_scores
            from app.modules.score.schemas import ScoreRequest
            
            # 创建评分请求，对刚生成的图片进行评分
            score_request = ScoreRequest(original_image_id=result[0])
            score_response = create_scores(db, score_request)
            print(f"自动评分完成，共评分 {score_response.scored_count} 张生成图片")
        except Exception as score_error:
            print(f"自动评分失败: {score_error}")
            # 评分失败不影响生成流程，继续返回成功结果
        
        return GenerationResponse(
            original_image_id=result[0],
            generated_count=generated_count,
            message=f"成功为用户 {username} 生成 {generated_count} 张图片"
        )
        
    except Exception as e:
        db.rollback()
        print(f"生成任务失败: {e}")
        raise ValueError(f"生成失败: {str(e)}")

def get_generated_images(db: Session, original_image_id: int) -> List[GeneratedImageInfo]:
    """获取生成的图片列表"""
    results = db.execute(text("""
        SELECT id, filename, file_path, created_at 
        FROM generated_images 
        WHERE original_image_id = :original_image_id
        ORDER BY created_at DESC
    """), {"original_image_id": original_image_id}).fetchall()
    
    return [
        GeneratedImageInfo(
            id=row[0],
            filename=row[1],
            file_path=row[2],
            created_at=row[3]
        ) for row in results
    ]