"""
打分服务
"""
import random
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.modules.score.schemas import ScoreRequest, ScoreResponse, ScoreInfo, GeneratedImageScore

def create_scores(db: Session, request: ScoreRequest) -> ScoreResponse:
    """为生成的图片创建评分"""
    
    try:
        # 获取原始图片对应的所有生成图片
        generated_images = db.execute(text("""
            SELECT gi.id, gi.filename, gi.file_path, gi.created_at, i.user_id, u.username
            FROM generated_images gi
            JOIN images i ON gi.original_image_id = i.id
            JOIN users u ON i.user_id = u.id
            WHERE gi.original_image_id = :original_image_id
            ORDER BY gi.created_at DESC
        """), {"original_image_id": request.original_image_id}).fetchall()
        
        if not generated_images:
            raise ValueError("未找到对应的生成图片")
        
        user_id = generated_images[0][4]
        username = generated_images[0][5]
        
        scored_count = 0
        
        for generated_image in generated_images:
            generated_image_id = generated_image[0]
            
            # 检查是否已经评分过
            existing_score = db.execute(text("""
                SELECT id FROM image_evaluations 
                WHERE generated_image_id = :generated_image_id
            """), {"generated_image_id": generated_image_id}).fetchone()
            
            if existing_score:
                # 如果已经评分过，跳过
                continue
            
            # 生成1-100的随机分数
            random_score = random.randint(1, 100)
            
            # 插入评分记录
            db.execute(text("""
                INSERT INTO image_evaluations 
                (generated_image_id, overall_score, highlights, ai_comment, shooting_guidance, created_at)
                VALUES (:generated_image_id, :overall_score, :highlights, :ai_comment, :shooting_guidance, NOW())
            """), {
                "generated_image_id": generated_image_id,
                "overall_score": random_score,
                "highlights": f"随机评分: {random_score}分",
                "ai_comment": f"这是一张评分为{random_score}分的生成图片",
                "shooting_guidance": f"基于{random_score}分的拍摄建议"
            })
            
            scored_count += 1
        
        if scored_count == 0:
            raise ValueError("所有图片都已评分过")
        
        db.commit()
        
        return ScoreResponse(
            original_image_id=request.original_image_id,
            scored_count=scored_count,
            message=f"成功为用户 {username} 的 {scored_count} 张生成图片进行评分"
        )
        
    except Exception as e:
        db.rollback()
        print(f"评分失败: {e}")
        raise ValueError(f"评分失败: {str(e)}")

def get_scores_by_original_image(db: Session, original_image_id: int) -> List[GeneratedImageScore]:
    """获取原始图片对应的所有生成图片的评分"""
    results = db.execute(text("""
        SELECT 
            gi.id as generated_image_id,
            gi.filename,
            gi.file_path,
            ie.overall_score,
            gi.created_at
        FROM generated_images gi
        LEFT JOIN image_evaluations ie ON gi.id = ie.generated_image_id
        WHERE gi.original_image_id = :original_image_id
        ORDER BY gi.created_at DESC
    """), {"original_image_id": original_image_id}).fetchall()
    
    return [
        GeneratedImageScore(
            generated_image_id=row[0],
            filename=row[1],
            file_path=row[2],
            overall_score=row[3] if row[3] is not None else 0,
            created_at=row[4]
        ) for row in results
    ]

def get_score_details(db: Session, generated_image_id: int) -> ScoreInfo:
    """获取特定生成图片的详细评分信息"""
    result = db.execute(text("""
        SELECT 
            ie.id,
            ie.generated_image_id,
            ie.overall_score,
            ie.highlights,
            ie.ai_comment,
            ie.shooting_guidance,
            ie.created_at
        FROM image_evaluations ie
        WHERE ie.generated_image_id = :generated_image_id
    """), {"generated_image_id": generated_image_id}).fetchone()
    
    if not result:
        raise ValueError("未找到评分信息")
    
    return ScoreInfo(
        id=result[0],
        generated_image_id=result[1],
        overall_score=result[2],
        highlights=result[3],
        ai_comment=result[4],
        shooting_guidance=result[5],
        created_at=result[6]
    )
