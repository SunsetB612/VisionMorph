"""
生成服务
"""
import os
import sys
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
# 生成服务 - 处理图片生成逻辑
from app.modules.generate.schemas import GenerationRequest, GenerationResponse, GeneratedImageInfo

# 添加 DiffSynth-Studio 目录到路径以导入 pi.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'DiffSynth-Studio'))
from pi import generate_prompts_with_doubao, qwen_generate_images_from_prompts


def create_generation(db: Session, request: GenerationRequest) -> GenerationResponse:
    """创建生成任务 - 集成 pi.py 模块"""
    
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
        
        original_image_id = result[0]
        original_file_path = result[2]
        user_id = result[3]
        username = result[4]
        
        # 处理用户选择的视角
        view_angles_list = request.view_angles if request.view_angles else ["不限"]
        view_angles_str = ','.join(view_angles_list)
        print(f"用户选择的视角: {view_angles_str}")
        
        if not os.path.exists(original_file_path):
            raise ValueError(f"原始图片文件不存在: {original_file_path}")
        
        # 创建用户目录结构
        from app.modules.upload.services import UploadService
        dirs = UploadService.create_user_directories(user_id)
        results_dir = dirs["results_dir"]
        
        # 创建prompts目录
        user_base_dir = os.path.dirname(results_dir)  # static/userX/
        prompts_dir = os.path.join(user_base_dir, "prompts")
        os.makedirs(prompts_dir, exist_ok=True)
        
        # ==================== 第一步：使用 pi.py 生成 Prompts ====================
        print(f"\n🔄 开始调用 pi.py 生成 Prompts...")
        
        # 从环境变量获取豆包 API Key（或使用配置文件）
        api_key = os.getenv("DOUBAO_API_KEY", "1b2e7082-a359-4e1a-9c3b-f7c1349b9d3f")
        
        try:
            # 调用 pi.py 的 prompt 生成函数
            # 注意：pi.py 的函数会自动保存 prompt 文件到 static/user{id}/prompts/ 目录
            generated_prompts = generate_prompts_with_doubao(
                api_key=api_key,
                local_image_path=original_file_path,
                user_selected_views=view_angles_list,
                user_id=user_id  # 传入用户ID以保存到对应目录
            )
            
            print(f"✅ 成功生成 {len(generated_prompts)} 个 Prompts")
            
        except Exception as prompt_error:
            print(f"⚠️  Prompt 生成失败，使用兜底方案: {prompt_error}")
            # 如果 API 调用失败，函数内部会自动使用兜底 prompts
            generated_prompts = []
        
        # ==================== 第二步：使用 pi.py 生成图片 ====================
        print(f"\n🔄 开始调用 pi.py 生成图片...")
        
        try:
            # 调用 pi.py 的图片生成函数
            # 注意：该函数会读取刚才保存的 prompt 文件，生成图片到 static/user{id}/results/ 目录
            qwen_generate_images_from_prompts(user_id=user_id)
            
            print(f"✅ 图片生成完成")
            
        except Exception as image_error:
            raise ValueError(f"图片生成失败: {str(image_error)}")
        
        # ==================== 第三步：将生成的文件记录到数据库 ====================
        print(f"\n🔄 将生成的文件记录到数据库...")
        
        # 获取刚才生成的 prompt 文件列表
        prompt_files = sorted([f for f in os.listdir(prompts_dir) if f.startswith(f"user{user_id}_") and f.endswith('.txt')])
        
        # 获取刚才生成的图片文件列表
        generated_image_files = sorted([f for f in os.listdir(results_dir) if f.startswith(f"user{user_id}_") and f.endswith('.jpg')])
        
        generated_count = 0
        
        # 配对 prompt 和 生成的图片（根据时间戳匹配）
        for img_file in generated_image_files:
            try:
                # 提取时间戳，用于匹配对应的 prompt 文件
                # 图片命名格式：user{id}_img_{序号}_{timestamp}_generated_{i}.jpg
                # Prompt命名格式：user{id}_img_{序号}_{timestamp}_prompt_{i}.txt
                
                img_file_path = os.path.join(results_dir, img_file)
                
                # 查找对应的 prompt 文件（通过时间戳匹配）
                img_parts = img_file.replace('_generated_', '_SPLIT_').split('_SPLIT_')
                if len(img_parts) >= 2:
                    prompt_prefix = img_parts[0]  # user{id}_img_{序号}_{timestamp}
                    prompt_suffix = img_parts[1].replace('.jpg', '.txt')  # {i}.txt
                    
                    matching_prompt_file = f"{prompt_prefix}_prompt_{prompt_suffix}"
                    prompt_file_path = os.path.join(prompts_dir, matching_prompt_file)
                else:
                    # 如果解析失败，尝试直接匹配
                    prompt_file_path = None
                
                # 检查 prompt 文件是否存在
                if not prompt_file_path or not os.path.exists(prompt_file_path):
                    print(f"⚠️  未找到对应的 prompt 文件: {img_file}")
                    prompt_file_path = None
                
                # 保存到数据库
                db.execute(text("""
                    INSERT INTO generated_images (original_image_id, filename, file_path, view_angles, prompt_file_path, created_at)
                    VALUES (:original_image_id, :filename, :file_path, :view_angles, :prompt_file_path, NOW())
                """), {
                    "original_image_id": original_image_id,
                    "filename": img_file,
                    "file_path": img_file_path,
                    "view_angles": view_angles_str,
                    "prompt_file_path": prompt_file_path
                })
                generated_count += 1
                
            except Exception as e:
                print(f"记录图片 {img_file} 失败: {e}")
                continue
        
        if generated_count == 0:
            raise ValueError("没有成功生成任何图片")
        
        db.commit()
        
        # 自动为刚生成的图片进行评分
        try:
            from app.modules.score.services import create_scores
            from app.modules.score.schemas import ScoreRequest
            
            # 创建评分请求，对刚生成的图片进行评分
            score_request = ScoreRequest(original_image_id=original_image_id)
            score_response = create_scores(db, score_request)
            print(f"✅ 自动评分完成，共评分 {score_response.scored_count} 张生成图片")
        except Exception as score_error:
            print(f"⚠️  自动评分失败: {score_error}")
            # 评分失败不影响生成流程，继续返回成功结果
        
        return GenerationResponse(
            original_image_id=original_image_id,
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
        SELECT id, filename, file_path, view_angles, prompt_file_path, created_at 
        FROM generated_images 
        WHERE original_image_id = :original_image_id
        ORDER BY created_at DESC
    """), {"original_image_id": original_image_id}).fetchall()
    
    images = []
    for row in results:
        # 读取prompt文件内容
        prompt_content = None
        prompt_file_path = row[4]
        if prompt_file_path and os.path.exists(prompt_file_path):
            try:
                with open(prompt_file_path, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
            except Exception as e:
                print(f"读取prompt文件失败 {prompt_file_path}: {e}")
        
        images.append(GeneratedImageInfo(
            id=row[0],
            filename=row[1],
            file_path=row[2],
            view_angles=row[3],
            prompt_file_path=prompt_file_path,
            prompt_content=prompt_content,
            created_at=row[5]
        ))
    
    return images