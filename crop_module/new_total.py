import cv2
import numpy as np
import torch
import torchvision
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt
import os
import sys
import pandas as pd
from transformers import CLIPModel, CLIPProcessor, BertTokenizer, BertForSequenceClassification
import ssl
import requests
import base64
import json
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from torch.optim import AdamW
from docx import Document
from pathlib import Path

# 基础环境配置
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
ssl._create_default_https_context = ssl._create_unverified_context  # 解决HTTPS证书问题

MODULE_ROOT = Path(__file__).resolve().parent
DEFAULT_RESOURCE_ROOT = MODULE_ROOT


# ========== 1. 豆包API调用工具类 ==========
class DoubaoAPIClient:
    def __init__(self, api_key, model="doubao-seed-1-6-251015"):
        self.api_key = api_key
        self.model = model

        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.session = requests.Session()
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries=3))

    def image_to_base64(self, image_np):
        """将numpy图像转为base64"""
        try:
            success, img_encoded = cv2.imencode(".jpg", image_np, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if not success:
                return "图片编码失败"
            return base64.b64encode(img_encoded).decode("utf-8")
        except Exception as e:
            return f"图片编码失败: {str(e)}"

    def get_shooting_suggestions(self, original_img, crop_img, region_type, coords, direction_desc):
        """调用豆包API生成拍摄建议"""
        # 编码图片
        original_base64 = self.image_to_base64(original_img)
        crop_base64 = self.image_to_base64(crop_img)
        
        if "失败" in original_base64 or "失败" in crop_base64:
            return f"图片处理错误：原始图({original_base64}) | 裁剪图({crop_base64})"

        # 优化提示词
        prompt = f"""
        你是专业摄影构图指导专家，需生成详细、规范且易懂的拍摄建议，语言适度书面化，避免过于口语化或随意表述，总长度不少于500字，且仅输出纯文字内容：
        1. 格式要求：删除所有Markdown格式元素（包括星号、井号、列表符号、括号嵌套等），仅用段落式纯文字呈现，段落间可适当换行区分逻辑；
        2. 分析裁剪图优点：结合画面元素、构图逻辑、色彩搭配等维度，具体说明优势所在，如主体定位精准、画面平衡感良好、色彩过渡自然等，避免笼统表述；
        3. 指出裁剪图不足：客观说明存在的问题，如主体边缘留白不足、画面比例不够协调、背景元素略显杂乱等，表述中肯且不生硬；
        4. 给出具体优化建议：结合原始全景图和方位说明，从拍摄角度调整、焦距选择、主体位置摆放、背景取舍等方面展开，每条建议需包含操作方法和优化原理，确保可落地；
        5. 补充延伸技巧：增加2-3条与场景适配的摄影技巧，如光线利用、层次感营造、画面元素取舍等，丰富建议的实用性；
        6. 整体要求：结构清晰、语言流畅规范，兼顾专业性和可读性，适配摄影爱好者理解和操作，无任何格式符号干扰阅读。
    
        补充信息：
        - 裁剪区域类型：{region_type}
        - 裁剪坐标（左上角x,y；右下角x2,y2）：{coords}
        - 方位说明：{direction_desc}
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url", 
                        "image_url": f"data:image/jpeg;base64,{original_base64}"
                    },
                    {
                        "type": "image_url", 
                        "image_url": f"data:image/jpeg;base64,{crop_base64}"
                    },
                    {
                        "type": "text", 
                        "text": prompt
                    }
                ]
            }
        ]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": messages,
            "stream": False
        }

        try:
            response = self.session.post(
                self.api_url, 
                headers=headers, 
                json=data,
                timeout=3000
            )
            
            # 详细调试信息
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text[:500]}...")
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return f"API返回格式异常: {json.dumps(result, ensure_ascii=False)[:200]}"
                
        except requests.exceptions.HTTPError as http_err:
            error_detail = f"HTTP错误 {response.status_code}: "
            try:
                error_json = response.json()
                error_detail += error_json.get("error", {}).get("message", str(http_err))
            except:
                error_detail += response.text[:200]
            return error_detail
            
        except requests.exceptions.ConnectionError:
            return "网络连接失败：请检查网络连接和DNS配置"
        except Exception as e:
            return f"API调用失败：{str(e)}"


# ========== 2. 读取Word文档方位说明（保持兼容） ==========
def read_direction_desc(docx_path):
    """读取docx中的方位说明文本"""
    try:
        if not os.path.exists(docx_path):
            return f"方位说明文档不存在：{docx_path}"
        doc = Document(docx_path)
        # 提取所有段落文本（忽略空段落）
        direction_desc = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
        return direction_desc if direction_desc else "文档无有效方位说明"
    except Exception as e:
        return f"文档读取失败：{str(e)}（建议检查文档是否为标准docx格式）"


# ========== 3. 全景图裁剪功能 ==========
class PanoramaCropper:
    def __init__(self, yolo_path=None):
        self.srm_model = self._load_srm_model()
        self.yolo_model = self._load_yolo_model(yolo_path)
        self.segmentation_model = self._load_segmentation_model()
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.priority_classes = {'person': 0, 'cat': 15, 'dog': 16, 'car': 2, 'bicycle': 1, 
                                 'bird': 14, 'flower': 58, 'tree': 59, 'building': 66}
    
    def _load_srm_model(self):
        class SimpleSRM(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = torch.nn.Conv2d(3, 64, kernel_size=3, padding=1)
                self.conv2 = torch.nn.Conv2d(64, 32, kernel_size=3, padding=1)
                self.conv3 = torch.nn.Conv2d(32, 1, kernel_size=3, padding=1)
                self.relu = torch.nn.ReLU()
            def forward(self, x):
                x = self.relu(self.conv1(x))
                x = self.relu(self.conv2(x))
                x = torch.sigmoid(self.conv3(x))
                return x
        model = SimpleSRM()
        model.eval()
        return model
    
    def _load_yolo_model(self, yolo_path):
        if yolo_path is None:
            print("正在加载YOLOv5模型（在线下载）...")
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        else:
            if not os.path.exists(yolo_path):
                raise FileNotFoundError(f"YOLOv5路径不存在: {yolo_path}")
            print(f"正在从本地加载YOLOv5模型: {yolo_path}")
            sys.path.insert(0, yolo_path)
            try:
                model = torch.hub.load(yolo_path, 'yolov5s', source='local', pretrained=True)
            except Exception as e:
                print(f"本地加载失败: {e}，尝试在线下载...")
                model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        model.eval()
        return model
    
    def _load_segmentation_model(self):
        model = torchvision.models.segmentation.deeplabv3_resnet50(pretrained=True)
        model.eval()
        return model
    
    def frequency_tuned_saliency(self, image):
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_mean, a_mean, b_mean = np.mean(l), np.mean(a), np.mean(b)
        saliency = np.sqrt(np.square(l - l_mean) + np.square(a - a_mean) + np.square(b - b_mean))
        saliency = (saliency - np.min(saliency)) / (np.max(saliency) - np.min(saliency)) * 255
        return saliency.astype(np.uint8)
    
    def srm_saliency_detection(self, image):
        img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        img_tensor = self.transform(img).unsqueeze(0)
        with torch.no_grad():
            output = self.srm_model(img_tensor)
        saliency_map = output.squeeze().numpy()
        saliency_map = (saliency_map * 255).astype(np.uint8)
        saliency_map = cv2.resize(saliency_map, (image.shape[1], image.shape[0]))
        return saliency_map
    
    def object_detection(self, image):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.yolo_model(rgb_image)
        return results.pandas().xyxy[0]
    
    def image_segmentation(self, image):
        img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        img_tensor = self.transform(img).unsqueeze(0)
        with torch.no_grad():
            output = self.segmentation_model(img_tensor)['out']
        pred = torch.argmax(output, dim=1).squeeze().numpy()
        pred = cv2.resize(pred, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
        return pred
    
    def get_potential_regions(self, image, method='frequency_tuned'):
        if method == 'frequency_tuned':
            saliency_map = self.frequency_tuned_saliency(image)
        elif method == 'srm':
            saliency_map = self.srm_saliency_detection(image)
        else:
            saliency_map = self.frequency_tuned_saliency(image)
        
        potential_regions = []
        _, binary_saliency = cv2.threshold(saliency_map, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary_saliency, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) > 800:
                x, y, w, h = cv2.boundingRect(contour)
                potential_regions.append((x, y, w, h, 'saliency'))
        
        try:
            detections = self.object_detection(image)
            if hasattr(detections, 'iterrows'):
                for _, row in detections.iterrows():
                    confidence = row.get('confidence', 0)
                    class_name = row.get('name', '')
                    x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                    w, h = x2 - x1, y2 - y1
                    if (class_name in self.priority_classes and confidence > 0.4) or (confidence > 0.6):
                        if w * h > 400:
                            potential_regions.append((x1, y1, w, h, f'object_{class_name}'))
        except Exception as e:
            print(f"目标检测失败: {e}")
        
        try:
            segmentation = self.image_segmentation(image)
            unique_classes, counts = np.unique(segmentation, return_counts=True)
            top_classes = unique_classes[np.argsort(counts)[-3:]]
            for cls in top_classes:
                if cls == 0:
                    continue
                mask = (segmentation == cls).astype(np.uint8) * 255
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > 1200:
                        x, y, w, h = cv2.boundingRect(contour)
                        potential_regions.append((x, y, w, h, 'segmentation'))
        except Exception as e:
            print(f"图像分割失败: {e}")
        
        return potential_regions, saliency_map, segmentation
    
    def crop_regions(self, image, regions, top_n=5):
        if not regions:
            h, w = image.shape[:2]
            regions = [
                (0, 0, w//2, h//2, 'default'),
                (w//2, 0, w//2, h//2, 'default'),
                (0, h//2, w//2, h//2, 'default'),
                (w//2, h//2, w//2, h//2, 'default'),
                (w//4, h//4, w//2, h//2, 'default_center')
            ]
        
        unique_regions = []
        seen = set()
        for x, y, w, h, rtype in regions:
            key = (round(x/50), round(y/50), round(w/50), round(h/50))
            if key not in seen:
                seen.add(key)
                unique_regions.append((x, y, w, h, rtype))
        
        def region_priority(region):
            rtype = region[4]
            area = region[2] * region[3]
            if rtype.startswith('object'):
                return (10, area)
            elif rtype == 'segmentation':
                return (5, area)
            else:
                return (1, area)
        
        unique_regions.sort(key=region_priority, reverse=True)
        cropped_images = []
        
        for i, (x, y, w, h, rtype) in enumerate(unique_regions[:top_n]):
            x = max(0, x)
            y = max(0, y)
            x2 = min(image.shape[1], x + w)
            y2 = min(image.shape[0], y + h)
            if x2 > x and y2 > y:
                cropped = image[y:y2, x:x2]
                cropped_images.append((cropped, rtype, (x, y, x2, y2)))
        
        while len(cropped_images) < top_n:
            h, w = image.shape[:2]
            default_regions = [
                (w//6, h//6, 2*w//3, 2*h//3, 'default_supplement'),
                (0, h//3, w//2, 2*h//3, 'default_supplement'),
                (w//2, h//3, w//2, 2*h//3, 'default_supplement')
            ]
            for reg in default_regions:
                if len(cropped_images) >= top_n:
                    break
                x, y, w_reg, h_reg, rtype = reg
                x2 = x + w_reg
                y2 = y + h_reg
                cropped = image[y:y2, x:x2]
                cropped_images.append((cropped, rtype, (x, y, x2, y2)))
        
        return cropped_images
    
    def process_panorama(self, image_path, top_n=5):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}（请检查路径是否正确）")
        regions, saliency_map, segmentation = self.get_potential_regions(image)
        cropped_regions = self.crop_regions(image, regions, top_n)
        return {
            'original': image,
            'saliency_map': saliency_map,
            'segmentation': segmentation,
            'cropped_regions': cropped_regions
        }


# ========== 4. 构图分析功能 ==========
class MultimodalCompositionAnalyzer:
    def __init__(self, bert_dir=None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.resource_root = DEFAULT_RESOURCE_ROOT
        self.local_clip_dir = str(self.resource_root / "clip-vit-base-patch32")
        if not os.path.exists(self.local_clip_dir):
            raise FileNotFoundError(f"CLIP模型目录不存在：{self.local_clip_dir}")
        try:
            print(f"正在加载本地CLIP模型：{self.local_clip_dir}")
            self.clip_model = CLIPModel.from_pretrained(self.local_clip_dir).to(self.device)
            self.clip_processor = CLIPProcessor.from_pretrained(self.local_clip_dir)
        except Exception as e:
            raise RuntimeError(f"加载CLIP模型失败：{str(e)}")
        
        self.composition_aspects = [
            "良好的构图", "糟糕的构图", "平衡的构图", "不平衡的构图",
            "主体突出", "主体不突出", "适当的留白", "过多的留白",
            "良好的层次感", "缺乏层次感", "清晰的视觉引导", "混乱的视觉引导",
            "黄金比例构图", "不符合黄金比例", "对称构图", "不对称构图",
            "前景虚化", "无前景", "背景简洁", "背景杂乱",
            "色彩协调", "色彩冲突", "明暗对比适中", "过亮", "过暗"
        ]
        
        self.local_bert_dir = (
            bert_dir if bert_dir else str(self.resource_root / "bert-base-chinese")
        )
        try:
            print(f"正在加载BERT模型：{self.local_bert_dir}")
            self.bert_tokenizer = BertTokenizer.from_pretrained(self.local_bert_dir, local_files_only=True)
            self.bert_model = BertForSequenceClassification.from_pretrained(
                self.local_bert_dir, num_labels=1, local_files_only=True
            ).to(self.device)
        except Exception as e:
            raise RuntimeError(f"BERT模型加载失败：{str(e)}")
        
        self.style_labels = [
            "简约", "复杂", "对称", "不对称", "动态", "静态",
            "紧凑", "松散", "平衡", "对比强烈", "柔和"
        ]
    
    def load_image(self, image_np):
        image = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
        inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)
        return inputs["pixel_values"]
    
    def frequency_tuned_saliency(self, image):
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_mean, a_mean, b_mean = np.mean(l), np.mean(a), np.mean(b)
        saliency = np.sqrt(np.square(l - l_mean) + np.square(a - a_mean) + np.square(b - b_mean))
        saliency = (saliency - np.min(saliency)) / (np.max(saliency) - np.min(saliency)) * 255
        return saliency.astype(np.uint8)
    
    def get_image_caption(self, image):
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(pixel_values=image)
            text_templates = [
                "a photo with {}", 
                "an image with {}", 
                "a picture with {}", 
                "a shot with {}"
            ]
            text_list = []
            for comp_aspect in self.composition_aspects:
                for template in text_templates:
                    text_list.append(template.format(comp_aspect))
            
            text_inputs = self.clip_processor(
                text=text_list,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)
            text_features = self.clip_model.get_text_features(**text_inputs)
            
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            values, indices = similarity[0].topk(5)
            
            caption_parts = []
            seen_captions = set()
            for idx in indices:
                orig_idx = idx // len(text_templates)
                caption = self.composition_aspects[orig_idx]
                if caption not in seen_captions:
                    seen_captions.add(caption)
                    caption_parts.append(caption)
                if len(caption_parts) >= 5:
                    break
            return ", ".join(caption_parts)
    
    def predict_style(self, image):
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(pixel_values=image)
            text_list = [f"a photo with {s} style" for s in self.style_labels]
            text_inputs = self.clip_processor(text=text_list, return_tensors="pt", padding=True, truncation=True).to(self.device)
            text_features = self.clip_model.get_text_features(**text_inputs)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            values, indices = similarity[0].topk(3)
            styles = [(self.style_labels[idx], float(values[i])) for i, idx in enumerate(indices)]
            return styles
    
    def get_composition_score(self, caption, image_crop):
        inputs = self.bert_tokenizer(
            caption, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=512
        ).to(self.device)
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            score = outputs.logits.item()
        
        h, w = image_crop.shape[:2]
        saliency_map = self.frequency_tuned_saliency(image_crop)
        _, binary = cv2.threshold(saliency_map, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        subject_ratio = np.sum(binary > 0) / (h * w)
        if 0.3 < subject_ratio < 0.7:
            score += 1.2
        elif 0.2 < subject_ratio <= 0.3 or 0.7 <= subject_ratio < 0.8:
            score += 0.5
        elif subject_ratio <= 0.2 or subject_ratio >= 0.8:
            score -= 0.8
        
        aspect_ratio = w / h
        ideal_ratios = [16/9, 4/3, 1.0, 3/4, 9/16]
        min_diff = min(abs(aspect_ratio - r) for r in ideal_ratios)
        score += (0.5 - min_diff) * 3
        
        edge_margin = min(h, w) * 0.1
        edge_mask = np.zeros_like(binary)
        edge_mask[:int(edge_margin), :] = 1
        edge_mask[-int(edge_margin):, :] = 1
        edge_mask[:, :int(edge_margin)] = 1
        edge_mask[:, -int(edge_margin):] = 1
        edge_subject_ratio = np.sum((binary > 0) & (edge_mask == 1)) / (np.sum(binary > 0) + 1e-6)
        if edge_subject_ratio > 0.3:
            score -= 0.6
        
        score = np.clip(score, 0, 10)
        return round(score, 1)
    
    def generate_suggestions(self, caption, styles):
        suggestions = []
        if "主体不突出" in caption:
            suggestions.append("建议突出主体，可以通过调整焦距或构图来实现")
        if "不平衡的构图" in caption:
            suggestions.append("构图略显不平衡，尝试将主体放在黄金分割点位置")
        if "过多的留白" in caption:
            suggestions.append("留白过多，可以考虑缩小取景范围")
        if "缺乏层次感" in caption:
            suggestions.append("缺乏层次感，尝试调整拍摄角度或增加前景元素")
        if "背景杂乱" in caption:
            suggestions.append("背景较为杂乱，建议更换简洁背景或使用大光圈虚化背景")
        if "色彩冲突" in caption:
            suggestions.append("色彩搭配存在冲突，可调整白平衡或后期调色统一色调")
        if not suggestions:
            suggestions.append("构图良好，保持当前风格即可")
        position_suggestions = [
            "向左平移约一米可以获得更好的背景",
            "向右微调可以平衡画面元素",
            "稍微降低拍摄高度可以增强主体表现力",
            "提高拍摄角度可以展现更多环境信息"
        ]
        suggestions.append(np.random.choice(position_suggestions))
        return suggestions
    
    def analyze(self, image_np):
        try:
            image = self.load_image(image_np)
            caption = self.get_image_caption(image)
            styles = self.predict_style(image)
            score = self.get_composition_score(caption, image_np)
            suggestions = self.generate_suggestions(caption, styles)
            return {
                "composition_score": score,
                "style_labels": [f"{s[0]}({s[1]:.2f})" for s in styles],
                "explanation": f"图像分析显示: {caption}",
                "suggestions": suggestions
            }
        except Exception as e:
            return {"error": f"分析过程出错: {str(e)}"}


# ========== 5. BERT微调优化 ==========
class CompositionDataset(Dataset):
    def __init__(self, data, tokenizer, max_len=128):
        self.data = data
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        encoding = self.tokenizer(
            item["text"], 
            return_tensors="pt", 
            padding="max_length", 
            truncation=True, 
            max_length=self.max_len
        )
        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(item["score"], dtype=torch.float32)
        }

def load_cadb_data(cadb_dir):
    elements_path = os.path.join(cadb_dir, "annotations", "composition_elements.json")
    scores_path = os.path.join(cadb_dir, "annotations", "composition_scores.json")
    
    if not os.path.exists(elements_path) or not os.path.exists(scores_path):
        raise FileNotFoundError("CADB标注文件缺失，请确认elements和scores文件是否存在")
    
    with open(elements_path, "r", encoding="utf-8") as f:
        elements = json.load(f)
    with open(scores_path, "r", encoding="utf-8") as f:
        scores = json.load(f)
    
    train_data = []
    for img_id in elements:
        if img_id not in scores:
            continue
        composition_tags = elements[img_id]
        text = ", ".join(composition_tags)
        score = scores[img_id]["mean"] * 2
        train_data.append({"text": text, "score": score})
    
    print(f"成功解析CADB数据：{len(train_data)}条样本")
    return train_data

def fine_tune_bert(train_data, bert_base_dir, save_dir, epochs=3):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = BertTokenizer.from_pretrained(bert_base_dir, local_files_only=True)
    model = BertForSequenceClassification.from_pretrained(
        bert_base_dir, 
        num_labels=1, 
        problem_type="regression"
    ).to(device)
    
    dataset = CompositionDataset(train_data, tokenizer)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
    optimizer = AdamW(model.parameters(), lr=1e-5)
    
    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            total_loss += loss.item()
            
            loss.backward()
            optimizer.step()
        
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{epochs}，训练损失：{avg_loss:.4f}")
        if avg_loss < 0.3:
            print("损失已足够低，提前停止微调")
            break
    
    os.makedirs(save_dir, exist_ok=True)
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)
    print(f"✅ BERT微调完成，模型保存至：{save_dir}")


# ========== 6. 主逻辑：串联所有功能 ==========
if __name__ == "__main__":
    # 1. 配置路径（根据实际情况调整）
    resource_root = DEFAULT_RESOURCE_ROOT
    example_dir = resource_root / "example"
    input_image_path = str(example_dir / "11.png")
    input_docx_path = str(example_dir / "11.docx")
    yolo_path = str(resource_root / "yolov5")
    cadb_dir = str(resource_root / "image-composition-assessment-dataset-cadb")
    bert_base_dir = str(resource_root / "bert-base-chinese")
    bert_finetuned_dir = str(resource_root / "bert-finetuned-cadb")
    output_dir = str(resource_root / "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. 关键配置：豆包API密钥
    DOUBAO_API_KEY = "1956a016-06a4-42b4-b86f-17c45a9fade0"
    doubao_client = DoubaoAPIClient(api_key=DOUBAO_API_KEY)
    
    # 3. 读取方位说明
    print("=== 步骤1：读取方位说明文档 ===")
    direction_desc = read_direction_desc(input_docx_path)
    print(f"方位说明：{direction_desc}")
    
    # 4. BERT模型微调
    print("\n=== 步骤2：检查BERT模型 ===")
    if not os.path.exists(bert_finetuned_dir) or not os.listdir(bert_finetuned_dir):
        print("正在加载CADB数据集并微调BERT...")
        train_data = load_cadb_data(cadb_dir)
        fine_tune_bert(train_data, bert_base_dir, bert_finetuned_dir, epochs=3)
    else:
        print(f"✅ 已找到微调后BERT模型：{bert_finetuned_dir}")
    
    # 5. 生成全景图裁剪
    print("\n=== 步骤3：生成裁剪图 ===")
    try:
        cropper = PanoramaCropper(yolo_path=yolo_path)
        crop_result = cropper.process_panorama(input_image_path, top_n=5)
        cropped_regions = crop_result['cropped_regions']
        original_image = crop_result['original']
        print(f"✅ 生成 {len(cropped_regions)} 张裁剪图")
    except Exception as e:
        print(f"❌ 裁剪图生成失败：{str(e)}")
        sys.exit(1)
    
    # 6. 构图分析+豆包API生成建议
    print("\n=== 步骤4：分析裁剪图并生成拍摄建议 ===")
    analyzer = MultimodalCompositionAnalyzer(bert_finetuned_dir)
    excel_data = {
        "图片名字": [],
        "构图分数": [],
        "裁剪类型": [],
        "方位说明": [],
        "豆包拍摄建议": []
    }
    
    for i, (cropped_img, region_type, coords) in enumerate(cropped_regions):
        img_name = f"图片{i+1}"
        crop_save_path = os.path.join(output_dir, f"cropped_{i+1}.jpg")
        cv2.imwrite(crop_save_path, cropped_img)
        print(f"\n正在处理 {img_name}（保存路径：{crop_save_path}）")
        
        analysis = analyzer.analyze(cropped_img)
        if "error" in analysis:
            print(f"❌ {img_name} 分析失败：{analysis['error']}")
            excel_data["图片名字"].append(img_name)
            excel_data["构图分数"].append("分析失败")
            excel_data["裁剪类型"].append(region_type)
            excel_data["方位说明"].append(direction_desc)
            excel_data["豆包拍摄建议"].append("构图分析失败，无法生成建议")
            continue
        
        print(f"🔍 正在调用豆包API生成建议...")
        coords_str = f"({coords[0]},{coords[1]})-({coords[2]},{coords[3]})"
        shooting_suggestions = doubao_client.get_shooting_suggestions(
            original_img=original_image,
            crop_img=cropped_img,
            region_type=region_type,
            coords=coords_str,
            direction_desc=direction_desc
        )
        
        # 记录结果
        print(f"✅ {img_name} 处理完成，分数：{analysis['composition_score']}")
        excel_data["图片名字"].append(img_name)
        excel_data["构图分数"].append(analysis["composition_score"])
        excel_data["裁剪类型"].append(region_type)
        excel_data["方位说明"].append(direction_desc)
        excel_data["豆包拍摄建议"].append(shooting_suggestions)
    
    # 7. 生成Excel结果
    print("\n=== 步骤5：生成分析报告 ===")
    df = pd.DataFrame(excel_data)
    excel_save_path = os.path.join(output_dir, "构图分析报告_含豆包建议.xlsx")
    df.to_excel(excel_save_path, index=False)
    
    # 8. 输出最终结果
    print(f"\n🎉 所有操作完成！")
    print(f"📁 裁剪图目录：{output_dir}")
    print(f"📊 分析报告：{excel_save_path}")
