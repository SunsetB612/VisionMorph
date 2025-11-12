"""
结果展示服务
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.modules.result.schemas import (
    ResultListResponse, 
    ResultDetailResponse, 
    ResultImageInfo, 
    ResultDetailInfo
)

def get_results_by_original_image(db: Session, original_image_id: int) -> ResultListResponse:
    """获取原始图片对应的所有生成图片结果，按评分从高到低排序"""
    
    try:
        # 获取原始图片信息
        original_image = db.execute(text("""
            SELECT id, user_id FROM images WHERE id = :original_image_id
        """), {"original_image_id": original_image_id}).fetchone()
        
        if not original_image:
            raise ValueError("未找到原始图片")
        
        # 获取所有生成图片及其评分，按评分从高到低排序
        results = db.execute(text("""
            SELECT
                ti.id AS generated_image_id,
                ri.id AS result_image_id,
                ri.filename,
                ri.file_path,
                COALESCE(ie.overall_score, 0) as overall_score,
                ie.highlights,
                ri.created_at
            FROM temp_images ti
            JOIN result_images ri ON ri.temp_image_id = ti.id
            LEFT JOIN image_evaluations ie ON ti.id = ie.generated_image_id
            WHERE ti.original_image_id = :original_image_id
            ORDER BY COALESCE(ie.overall_score, 0) DESC, ri.created_at DESC
        """), {"original_image_id": original_image_id}).fetchall()
        
        if not results:
            raise ValueError("未找到生成图片")
        
        # 构建结果列表
        result_list = []
        for row in results:
            result_list.append(ResultImageInfo(
                generated_image_id=row[0],
                result_image_id=row[1],
                filename=row[2],
                file_path=row[3],
                overall_score=row[4],
                highlights=row[5],
                created_at=row[6]
            ))
        
        return ResultListResponse(
            original_image_id=original_image_id,
            total_count=len(result_list),
            results=result_list
        )
        
    except Exception as e:
        print(f"获取结果列表失败: {e}")
        raise ValueError(f"获取结果列表失败: {str(e)}")

def get_result_detail(db: Session, generated_image_id: int) -> ResultDetailResponse:
    """获取特定生成图片的详细结果信息"""
    
    try:
        # 获取生成图片的详细信息
        result = db.execute(text("""
            SELECT
                ti.id AS generated_image_id,
                ri.id AS result_image_id,
                ri.filename,
                ri.file_path,
                COALESCE(ie.overall_score, 0) AS overall_score,
                ie.highlights,
                ie.ai_comment,
                ie.shooting_guidance,
                ri.created_at
            FROM temp_images ti
            JOIN result_images ri ON ri.temp_image_id = ti.id
            LEFT JOIN image_evaluations ie ON ti.id = ie.generated_image_id
            WHERE ti.id = :generated_image_id
        """), {"generated_image_id": generated_image_id}).fetchone()
        
        if not result:
            raise ValueError("未找到生成图片")
        
        # 构建详细信息
        detail_info = ResultDetailInfo(
            generated_image_id=result[0],
            result_image_id=result[1],
            filename=result[2],
            file_path=result[3],
            overall_score=result[4],
            highlights=result[5],
            ai_comment=result[6],
            shooting_guidance=result[7],
            created_at=result[8]
        )
        
        return ResultDetailResponse(result=detail_info)
        
    except Exception as e:
        print(f"获取结果详情失败: {e}")
        raise ValueError(f"获取结果详情失败: {str(e)}")

def get_user_results(db: Session, user_id: int, limit: int = 50) -> List[ResultListResponse]:
    """获取用户的所有结果，按原始图片分组"""
    
    try:
        # 获取用户的所有原始图片
        original_images = db.execute(text("""
            SELECT id FROM images 
            WHERE user_id = :user_id 
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"user_id": user_id, "limit": limit}).fetchall()
        
        if not original_images:
            return []
        
        # 为每个原始图片获取结果
        user_results = []
        for original_image in original_images:
            try:
                result = get_results_by_original_image(db, original_image[0])
                if result.total_count > 0:  # 只包含有生成图片的结果
                    user_results.append(result)
            except ValueError:
                # 如果某个原始图片没有生成图片，跳过
                continue
        
        return user_results
        
    except Exception as e:
        print(f"获取用户结果失败: {e}")
        raise ValueError(f"获取用户结果失败: {str(e)}")