# 🎨 VisionMorph - 智能构图系统

> 基于AI的智能构图系统，帮助用户通过上传图片获得专业的构图建议和优化后的图片

## ✨ 平台功能

### 🎯 智能构图分析
- **专业构图建议** - 基于AI算法分析图片构图，提供专业建议
- **构图规则识别** - 自动识别三分法、黄金比例、对称等构图规则
- **视觉平衡评估** - 分析图片的视觉平衡和焦点分布

### 🚀 多方案生成
- **一键生成** - 上传图片后自动生成多种构图方案
- **风格多样** - 支持不同风格和角度的构图建议
- **实时预览** - 即时查看生成效果

### 📊 智能评分系统
- **专业评分** - 基于摄影理论的智能评分算法
- **多维度评估** - 从构图、色彩、光影等多角度评分
- **排名展示** - 按评分高低自动排序展示

### 💡 拍摄指导
- **详细分析** - 每张图片的详细构图分析报告
- **改进建议** - 具体的拍摄改进建议和技巧
- **学习资源** - 构图知识和摄影技巧分享

## 🛠️ 技术栈
- 后端: Python + FastAPI
- 前端: React + TypeScript + Vite
- AI模块: 图片生成 + 智能评分 + 构图分析

## 快速开始

### 数据库初始化

在启动后端服务之前，需要先初始化数据库：

```bash
# 确保 MySQL 服务已启动，并创建数据库（如果不存在）
# CREATE DATABASE visionmorph CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 运行数据库初始化脚本
python -m app.core.database
```

**配置数据库连接**（可选）：
- 创建 `.env` 文件配置数据库连接信息，或直接修改 `app/core/config.py` 中的默认值
- 默认配置：`localhost:3306`，用户名 `root`，密码为空，数据库名 `visionmorph`

### 后端启动
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

### 访问地址
- 后端API: http://localhost:8000
- 前端应用: http://localhost:5173
- API文档: http://localhost:8000/docs