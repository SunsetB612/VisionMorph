import os
import json
import base64
import torch
import gc
from PIL import Image
from datetime import datetime
from volcenginesdkarkruntime import Ark
from diffsynth.pipelines.qwen_image import QwenImagePipeline, ModelConfig

# ==================== 全局配置（旧模式，已弃用）====================
# 注意：以下变量仅为兼容旧代码保留，新的用户隔离模式请使用 static/user{id}/ 目录结构
PROMPT_DIR = "generated_prompts"  # 旧模式：全局提示词目录（已弃用）
IMAGE_DIR = "new_images"          # 旧模式：全局图片目录（已弃用）

# 移除全局目录创建逻辑（新模式在函数内部按需创建用户专属目录）
# os.makedirs(PROMPT_DIR, exist_ok=True)
# os.makedirs(IMAGE_DIR, exist_ok=True)

# 新增：用户可选视角方向（网页端下拉框可直接对应此列表）
ALLOWED_VIEWS = ["俯视", "仰视", "平视", "右前方", "左前方", "不限"]

# ==================== 第一部分：本地生成提示词（新增用户视角限制）====================
def generate_prompts_with_doubao(api_key, local_image_path, user_selected_views="不限", user_id=None):
    """
    本地调用豆包生成提示词（支持多选视角方向限制）
    :param api_key: 豆包API Key
    :param local_image_path: 本地图片路径（格式：static/user{id}/original/xxx.jpg）
    :param user_selected_views: 用户选择的视角方向，支持单选或多选
                                - 单选：字符串，如"俯视"
                                - 多选：列表，如["俯视", "仰视", "右前方"]
                                - 默认"不限"，可选值见ALLOWED_VIEWS
    :param user_id: 用户ID（可选），如果传入则直接使用，否则从路径解析
    :return: 生成的提示词列表
    """
    # ===== 获取用户ID：优先使用传入的user_id，否则从路径解析 =====
    if user_id is None:
        import re
        match = re.search(r'static[/\\]user(\d+)[/\\]original', local_image_path)
        if not match:
            raise ValueError(f"❌ 无法从路径 {local_image_path} 解析用户ID，请确保路径格式为 static/userN/original/xxx.jpg")
        user_id = int(match.group(1))
        print(f"🆔 从路径解析到用户ID: {user_id}")
    else:
        print(f"🆔 使用传入的用户ID: {user_id}")
    
    # 新增：处理用户选择（支持单选和多选，确保鲁棒性）
    if isinstance(user_selected_views, str):
        # 单选情况
        if not user_selected_views or user_selected_views not in ALLOWED_VIEWS:
            user_selected_views = "不限"
        selected_views = [user_selected_views]
    elif isinstance(user_selected_views, list):
        # 多选情况
        if not user_selected_views:
            selected_views = ["不限"]
        else:
            # 过滤非法值，保留有效视角
            selected_views = [view for view in user_selected_views if view in ALLOWED_VIEWS]
            if not selected_views:  # 如果过滤后为空，默认"不限"
                selected_views = ["不限"]
    else:
        # 其他类型，默认"不限"
        selected_views = ["不限"]
    
    # 如果包含"不限"，则忽略其他选择
    if "不限" in selected_views:
        selected_views = ["不限"]
    
    print(f"📌 用户选择的视角方向：{selected_views}")
    
    # 定义用户专属提示词目录
    user_prompt_dir = f"static/user{user_id}/prompts"

    try:
        # 初始化豆包客户端（原有逻辑不变）
        client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key
        )
        
        # 本地图片转base64（原有逻辑不变）
        with open(local_image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{image_base64}"
        
        # 新增：构造视角限制指令（支持多选视角，融入原有提示词，不破坏格式）
        view_restriction = ""
        if selected_views != ["不限"]:
            if len(selected_views) == 1:
                # 单选情况
                view_restriction = f"【核心限制】所有输出的观察视角必须围绕「{selected_views[0]}」方向，不允许生成其他方向的视角。"
            else:
                # 多选情况
                views_text = "、".join(selected_views)
                view_restriction = f"【核心限制】所有输出的观察视角必须围绕「{views_text}」这些方向，不允许生成其他方向的视角。"
        
        # 调用豆包生成提示词（仅修改text内容，新增视角限制）
        response = client.chat.completions.create(
            model="doubao-seed-1-6-vision-250815",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {
                            "type": "text",
                            "text": f"""{view_restriction}图片来自一位摄影者的拍摄照片，请分析图片内容（包括景色和可能出现的人物）与摄影者的拍摄视角，输出其它你认为适合进行拍摄的观察视角，然后编写出提示词格式。具体要求和示例如下：
1. 比如你分析图片中出现了一个旋转楼梯，且当前图片的视角是正面平视旋转楼梯，那么你认为其它适合拍摄的视角可以包括从楼梯正上方俯视（对应的输出的提示词为“观察位置为画面中出现的旋转楼梯的正上方，观察视角为向下俯视，生成该视角图片时需要注意保留变化视角后的旋转楼梯的外观符合真实性和立体性，以及画面中本来就存在的某些事物也需要保留，且转换视角后的外观符合真实性......”），从楼梯右下方向上仰视（对应的输出的提示词为“观察位置为画面中出现的旋转楼梯的底部右侧且距离楼梯5米左右，观察视角为向上仰视45度，可以看到楼梯的侧面，生成该视角图片时需要注意保留变化视角后的旋转楼梯的外观符合真实性和立体性，以及画面中本来就出现的其它xxx需要同样......”），等等。
2. 每个输出的提示词格式的结果必须包含观察位置，主要的观察对象或者参照物对象，观察视角/方向/角度。选择的可转换的视角个数为4-8个，即输出的提示词的个数为4-8个。长度多于20字，不超过200字，纯中文，内容越便于理解、越详细清晰越好。
3. 直接输出“‘改变图片中风景的观察视角’+提示词”，不要添加其它内容。"""
                        }
                    ]
                }
            ]
        )
        
        # 提取提示词并逐条保存（修改保存路径为用户专属目录）
        prompts = [line.strip() for line in response.choices[0].message.content.strip().splitlines() if line.strip()]
        
        # 生成时间戳（毫秒）
        import time
        timestamp = int(time.time() * 1000)
        
        for idx, prompt in enumerate(prompts, 1):
            # 使用与generate模块一致的命名规则：user{user_id}_img_{序号}_{timestamp}_prompt_{i}.txt
            # 序号使用idx，因为这是同一批生成的提示词
            prompt_filename = f"user{user_id}_img_{idx:03d}_{timestamp}_prompt_{idx}.txt"
            prompt_path = os.path.join(user_prompt_dir, prompt_filename)  # 修改：使用用户专属目录
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)
        views_display = "、".join(selected_views) if selected_views != ["不限"] else "不限"
        print(f"✅ 豆包生成成功！共{len(prompts)}个提示词（符合{views_display}视角限制），已保存到 {user_prompt_dir} 目录")
        print(f"📌 提示词命名示例：user{user_id}_img_001_{timestamp}_prompt_1.txt")
        return prompts
    
    except Exception as e:
        print(f"❌ 豆包提示词生成失败：{str(e)}")
        # 新增：兜底提示词按用户视角适配（支持多选视角，原有兜底逻辑优化，匹配视角限制）
        def get_fallback_prompts_for_views(views):
            """根据选择的视角生成对应的兜底提示词"""
            if views == ["不限"]:
                return [
                    "改变图片中风景的观察视角：观察位置为图片中核心对象左侧10米处，视角为平视向右前方30度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，画面中原本存在的事物需要保留，画面比例真实，转换视角后的外观符合真实性和立体性。",
                    "改变图片中风景的观察视角：观察位置为图片中核心对象正上方20米处，视角为30度俯视，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，画面中原本存在的事物需要保留，细节清晰，转换视角后的外观符合真实性和立体性。",
                    "改变图片中风景的观察视角：观察位置为图片中核心对象右侧边缘，视角为45度仰视，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，画面中原本存在的事物需要保留，空间纵深感强，转换视角后的外观符合真实性和立体性。",
                    "改变图片中风景的观察视角：观察位置为图片中核心对象下方5米处，视角为20度仰视，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，画面中原本存在的事物需要保留，立体感真实，转换视角后的外观符合真实性和立体性。"
                ]
            
            # 为每个视角生成对应的兜底提示词
            fallback_prompts = []
            for view in views:
                if view == "俯视":
                    view_prompts = [
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的正上方20米处，观察视角为向下俯视30度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的比例和细节真实自然。",
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的正上方15米处，观察视角为向下俯视45度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的外观合理。"
                    ]
                elif view == "仰视":
                    view_prompts = [
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的下方，观察视角为向上仰视60度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的纵深感真实。",
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的底部，观察视角为向上仰视45度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的动态感自然。"
                    ]
                elif view == "平视":
                    view_prompts = [
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的左侧10米处，观察视角为向前平视，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的地平线自然。",
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的边上5米处，观察视角为向左平视，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的倒影清晰。"
                    ]
                elif view == "右前方":
                    view_prompts = [
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的左侧5米处，观察视角为向右前方平视45度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的比例协调。",
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的西北角，观察视角为向右前方平视30度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的布局自然。"
                    ]
                elif view == "左前方":
                    view_prompts = [
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的右侧10米处，观察视角为向左前方平视40度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的比例协调。",
                        "改变图片中风景的观察视角：观察位置为画面中核心对象的南侧，观察视角为向左前方平视45度，生成该视角图片时需保留所有出现的物品、建筑、风景、自然山水等等的纹理和细节，符合真实性和立体性，画面中原本存在的事物需要保留，转换视角后的布局自然。"
                    ]
                else:
                    continue  # 跳过未知视角
                
                fallback_prompts.extend(view_prompts)
            
            # 如果没有任何有效视角，返回默认提示词
            if not fallback_prompts:
                return get_fallback_prompts_for_views(["不限"])
            
            return fallback_prompts
        
        fallback_prompts = get_fallback_prompts_for_views(selected_views)
        
        # 生成时间戳（毫秒）
        import time
        timestamp = int(time.time() * 1000)
        
        # 保存兜底提示词（修改保存路径为用户专属目录）
        for idx, prompt in enumerate(fallback_prompts, 1):
            # 使用与generate模块一致的命名规则：user{user_id}_img_{序号}_{timestamp}_prompt_{i}.txt
            prompt_filename = f"user{user_id}_img_{idx:03d}_{timestamp}_prompt_{idx}.txt"
            prompt_path = os.path.join(user_prompt_dir, prompt_filename)  # 修改：使用用户专属目录
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)
        views_display = "、".join(selected_views) if selected_views != ["不限"] else "不限"
        print(f"⚠️  已使用{views_display}视角的兜底提示词，共{len(fallback_prompts)}个，保存到 {user_prompt_dir} 目录")
        print(f"📌 提示词命名示例：user{user_id}_img_001_{timestamp}_prompt_1.txt")
        return fallback_prompts

# ==================== 第二部分：服务器生成图片（完全沿用原有逻辑，无修改）====================
def qwen_generate_images_from_prompts(user_id=1):
    """
    读取用户专属提示词文件，生成对应的多视角图片
    
    路径逻辑：
      - 读取提示词：static/user{id}/prompts/user{id}_img_{序号}_{timestamp}_prompt_{i}.txt
      - 保存图片：static/user{id}/results/user{id}_img_{序号}_{timestamp}_generated_{i}.jpg
    
    :param user_id: 用户ID（必填），用于定位用户专属目录
    """
    # 1. 显存优化配置
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    gc.enable()

    # 2. 初始化Qwen-Image模型管道
    print("🔧 初始化Qwen-Image模型管道...")
    pipe = QwenImagePipeline.from_pretrained(
        torch_dtype=torch.bfloat16,
        device="cuda",
        model_configs=[
            ModelConfig(
                model_id="Qwen/Qwen-Image-Edit", 
                origin_file_pattern="transformer/diffusion_pytorch_model*.safetensors",
                offload_device="cpu",
                offload_dtype=torch.float8_e4m3fn
            ),
            ModelConfig(
                model_id="Qwen/Qwen-Image", 
                origin_file_pattern="text_encoder/model*.safetensors",
                offload_device="cpu",
                offload_dtype=torch.float8_e4m3fn
            ),
            ModelConfig(
                model_id="Qwen/Qwen-Image", 
                origin_file_pattern="vae/diffusion_pytorch_model.safetensors"
            ),
        ],
        tokenizer_config=None,
        processor_config=ModelConfig(model_id="Qwen/Qwen-Image-Edit", origin_file_pattern="processor/"),
    )
    pipe.device = torch.device('cuda:0')
    pipe.enable_vram_management()
    print("✅ Qwen-Image模型初始化完成")

    # 3. 从upload板块保存的目录加载图片
    # 【注释】原有的load_and_resize_image()函数已被注释，现在直接从upload板块的目录读取
    # 原因：upload板块已经完成了格式转换（RGBA→RGB白色背景）和尺寸对齐（64倍数）
    # def load_and_resize_image(max_size=768):
    #     input_filenames = ["images/1.jpg", "images/1.png"]
    #     for filename in input_filenames:
    #         if os.path.exists(filename):
    #             img = Image.open(filename)
    #             if img.mode == "RGBA":
    #                 img = img.convert("RGB")
    #                 print("📷 已将4通道图片转为3通道RGB")
    #             
    #             width, height = img.size
    #             print(f"📏 原图尺寸: {width}x{height}")
    #             
    #             # 缩放为模型兼容尺寸（64的倍数）
    #             scale = max_size / max(width, height)
    #             if scale < 1:
    #                 new_width = (int(width * scale) // 64) * 64
    #                 new_height = (int(height * scale) // 64) * 64
    #                 img = img.resize((new_width, new_height), Image.LANCZOS)
    #                 print(f"📐 已缩放到模型兼容尺寸: {new_width}x{new_height}")
    #             return img
    #     raise FileNotFoundError("❌ 未找到图片，请检查images目录下是否有1.jpg或1.png")
    
    def load_image_from_upload_directory(user_id=1):
        """
        从upload板块保存的目录读取图片
        upload板块已经完成：
        1. RGBA→RGB转换（白色背景）
        2. 尺寸对齐到64的倍数
        3. 统一保存为jpg格式
        """
        # upload板块的图片保存路径：static/user{id}/original/
        user_original_dir = f"static/user{user_id}/original"
        
        if not os.path.exists(user_original_dir):
            raise FileNotFoundError(f"❌ 未找到用户目录：{user_original_dir}，请先通过upload接口上传图片")
        
        # 获取该目录下最新的图片
        image_files = [f for f in os.listdir(user_original_dir) if f.endswith('.jpg')]
        if not image_files:
            raise FileNotFoundError(f"❌ 用户目录 {user_original_dir} 中没有图片，请先上传")
        
        # 按文件名排序，获取最新的（文件名包含时间戳）
        image_files.sort(reverse=True)
        latest_image = os.path.join(user_original_dir, image_files[0])
        
        print(f"📂 从upload目录读取图片: {latest_image}")
        img = Image.open(latest_image)
        width, height = img.size
        print(f"📏 图片尺寸: {width}x{height} (已由upload板块处理为64的倍数)")
        
        return img
    
    # 加载用户上传的原图
    my_image = load_image_from_upload_directory(user_id=user_id)
    img_width, img_height = my_image.size

    # 4. 读取提示词文件（用户隔离模式）
    user_prompt_dir = f"static/user{user_id}/prompts"
    print(f"\n📖 从 {user_prompt_dir} 目录读取提示词...")
    
    # 检查用户提示词目录是否存在
    if not os.path.exists(user_prompt_dir):
        raise FileNotFoundError(f"❌ 未找到用户目录：{user_prompt_dir}，请先通过本地生成提示词")
    
    # 获取该用户的所有提示词文件
    all_user_prompts = [f for f in os.listdir(user_prompt_dir) if f.startswith(f"user{user_id}_") and f.endswith(".txt")]
    
    if not all_user_prompts:
        raise FileNotFoundError(f"❌ 用户 {user_id} 的提示词目录为空，请先本地生成提示词")
    
    # 按文件名倒序排序，获取最新批次的时间戳
    all_user_prompts.sort(reverse=True)
    latest_file = all_user_prompts[0]
    # 从文件名中提取时间戳：user4_img_111_1761621991549_prompt_1.txt → 1761621991549
    timestamp = latest_file.split('_')[3]
    
    # 筛选出该时间戳对应的所有提示词文件
    prompt_files = [f for f in all_user_prompts if f"_{timestamp}_" in f]
    
    # 按文件名排序（确保 prompt_1, prompt_2, ... 的顺序）
    prompt_files.sort()
    
    # 读取提示词内容（保持与文件顺序一致）
    view_prompts = []
    for file in prompt_files:
        file_path = os.path.join(user_prompt_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            view_prompts.append(f.read().strip())
    print(f"✅ 成功读取{len(view_prompts)}个提示词（时间戳：{timestamp}，顺序与文件序号一致）")

    # 5. 定义用户专属的图片保存目录
    user_results_dir = f"static/user{user_id}/results"
    os.makedirs(user_results_dir, exist_ok=True)
    print(f"📂 图片将保存到：{user_results_dir}")

    # 6. 逐一生成图片（命名与提示词完全对应）
    print("\n🚀 开始生成多角度图片...")
    for idx, (prompt, prompt_file) in enumerate(zip(view_prompts, prompt_files), 1):
        # 提取核心文件名并替换 "_prompt_" 为 "_generated_"（与 generate 模块对齐）
        core_filename = os.path.splitext(prompt_file)[0].replace("_prompt_", "_generated_")
        image_filename = f"{core_filename}.jpg"
        image_path = os.path.join(user_results_dir, image_filename)
        
        try:
            # 生成图片
            edited_image = pipe(
                prompt, 
                edit_image=my_image, 
                seed=1,
                num_inference_steps=20,
                height=img_height,
                width=img_width
            )
            
            # 保存图片（与提示词文件名对应）
            edited_image.save(image_path)
            print(f"✅ 生成完成：")
            print(f"   提示词：{os.path.join(user_prompt_dir, prompt_file)}")
            print(f"   图片：{image_path}\n")
        
        except Exception as e:
            print(f"❌ 生成失败（{core_filename}）: {str(e)}\n")
        
        finally:
            # 强制清理显存
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            gc.collect()

    print("🎉 所有图片生成流程结束！")
    print(f"📌 关联示例：")
    print(f"   提示词：{user_prompt_dir}/{prompt_files[0]}")
    # 注意：图片名需要将 prompt 替换为 generated
    image_example = os.path.splitext(prompt_files[0])[0].replace("_prompt_", "_generated_") + ".jpg"
    print(f"   对应图片：{user_results_dir}/{image_example}")

# ==================== 执行入口（本地/服务器切换）====================
if __name__ == "__main__":
    # ===== 配置：用户ID（与upload板块对应）=====
    USER_ID = 1  # 默认用户ID，对应 static/user1/original/ 目录
    
    # ===== 本地电脑执行：生成提示词（逐条保存为文件）=====
    LOCAL_API_KEY = "1b2e7082-a359-4e1a-9c3b-f7c1349b9d3f"  # 你的豆包API Key
    
    # 【修改】从upload板块的目录读取图片（不再使用固定路径 images/1.jpg）
    # LOCAL_IMAGE_PATH = "images/1.jpg"  # 旧方式：固定路径
    
    # 新方式：从upload板块保存的目录读取最新图片
    user_original_dir = f"static/user{USER_ID}/original"
    if not os.path.exists(user_original_dir):
        print(f"❌ 错误：未找到用户目录 {user_original_dir}")
        print("请先通过 /api/upload 接口上传图片")
        exit(1)
    
    image_files = [f for f in os.listdir(user_original_dir) if f.endswith('.jpg')]
    if not image_files:
        print(f"❌ 错误：目录 {user_original_dir} 中没有图片")
        print("请先通过 /api/upload 接口上传图片")
        exit(1)
    
    # 获取最新上传的图片
    image_files.sort(reverse=True)
    LOCAL_IMAGE_PATH = os.path.join(user_original_dir, image_files[0])
    print(f"📂 使用图片: {LOCAL_IMAGE_PATH}")
    
    # 使用示例：
    # 单选：generate_prompts_with_doubao(LOCAL_API_KEY, LOCAL_IMAGE_PATH, "俯视")
    # 多选：generate_prompts_with_doubao(LOCAL_API_KEY, LOCAL_IMAGE_PATH, ["俯视", "仰视", "右前方"])
    # 不限：generate_prompts_with_doubao(LOCAL_API_KEY, LOCAL_IMAGE_PATH, "不限")
    generate_prompts_with_doubao(LOCAL_API_KEY, LOCAL_IMAGE_PATH)
    
    # ===== 服务器执行：生成图片（与提示词文件一对一关联）=====
    qwen_generate_images_from_prompts()
