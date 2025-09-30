# VisionMorph 项目结构

## 项目概述
VisionMorph 是一个基于AI的智能构图系统，帮助用户通过上传图片获得专业的构图建议和优化后的图片。

## 技术栈
- **后端**: Python + FastAPI
- **前端**: React + TypeScript + Vite
- **AI模块**: 图片生成 + 智能评分 + 构图分析
- **文件存储**: 本地文件系统

## 当前项目结构 (实际状态)
```
VisionMorph/
├── README.md                    # 项目说明文档
├── PROJECT_STRUCTURE.md         # 项目结构文档
├── requirements.txt             # Python依赖包
├── static/                      # 静态文件目录
│   ├── results/                 # 结果文件 (空)
│   ├── temp/                    # 临时文件 (空)
│   └── uploads/                 # 上传文件 (空)
├── app/                         # 后端应用核心代码
│   ├── main.py                  # FastAPI应用入口
│   ├── core/                    # 核心业务逻辑
│   ├── middleware/              # 中间件
│   └── modules/                 # 功能模块
│       ├── upload/              # 上传模块
│       ├── generate/            # 生成模块
│       ├── score/               # 评分模块
│       ├── result/              # 结果模块
│       └── user/                # 用户模块
└── frontend/                    # 前端React应用
    ├── src/                     # 源代码目录
    │   ├── main.tsx             # 应用入口 
    │   ├── App.tsx              # 主应用组件 
    │   ├── App.css              # 主样式 
    │   ├── index.css            # 全局样式 
    │   ├── components/          # 组件目录 ✅
    │   │   ├── upload/          # 上传模块 ✅
    │   │   │   ├── UploadComponent.tsx
    │   │   │   └── UploadComponent.css
    │   │   ├── generation/      # 生成模块 ✅
    │   │   │   ├── GenerationComponent.tsx
    │   │   │   └── GenerationComponent.css
    │   │   ├── results/         # 结果展示模块 ✅
    │   │   │   ├── ResultsComponent.tsx
    │   │   │   └── ResultsComponent.css
    │   │   ├── analysis/        # 分析模块 ✅
    │   │   │   ├── AnalysisComponent.tsx
    │   │   │   └── AnalysisComponent.css
    │   │   └── common/          # 通用组件 ✅
    │   │       ├── Button.tsx + Button.css
    │   │       └── Loading.tsx + Loading.css
    │   ├── pages/               # 页面组件 ✅
    │   │   ├── HomePage.tsx
    │   │   ├── UploadPage.tsx
    │   │   ├── ResultsPage.tsx
    │   │   └── AnalysisPage.tsx
    │   ├── hooks/               # 自定义Hooks ✅
    │   │   ├── useUpload.ts
    │   │   ├── useGeneration.ts
    │   │   └── useResults.ts
    │   ├── services/            # API服务 ✅
    │   │   ├── api.ts
    │   │   ├── uploadService.ts
    │   │   ├── generationService.ts
    │   │   ├── resultService.ts
    │   │   └── analysisService.ts
    │   ├── store/               # 状态管理 ✅
    │   │   ├── uploadStore.ts
    │   │   ├── generationStore.ts
    │   │   ├── resultStore.ts
    │   │   └── index.ts
    │   └── types/               # TypeScript类型定义 ✅
    │       ├── index.ts
    │       ├── upload.ts
    │       ├── generation.ts
    │       └── result.ts
    └── ...                      # 配置文件 (package.json, vite.config.ts等)
```

## 前端文件结构详情

### 🧩 Components 组件模块
- **upload/**: 图片上传组件
- **generation/**: 图片生成组件  
- **results/**: 结果展示组件
- **analysis/**: 构图分析组件
- **common/**: 通用组件 (Button, Loading)

### 📄 Pages 页面组件
- **HomePage**: 首页
- **UploadPage**: 上传页面
- **ResultsPage**: 结果页面
- **AnalysisPage**: 分析页面

### 🎣 Hooks 自定义钩子
- **useUpload**: 上传状态管理
- **useGeneration**: 生成状态管理
- **useResults**: 结果状态管理

### 🌐 Services API服务
- **api**: 基础API配置
- **uploadService**: 上传服务
- **generationService**: 生成服务
- **resultService**: 结果服务
- **analysisService**: 分析服务

### 🗃️ Store 状态管理
- **uploadStore**: 上传状态 (Zustand)
- **generationStore**: 生成状态 (Zustand)
- **resultStore**: 结果状态 (Zustand)

### 📝 Types 类型定义
- **通用类型**: API响应、文件、图片等
- **模块类型**: 上传、生成、结果相关类型

## 运行说明

### 后端启动
```bash
pip install -r requirements.txt
python -m app.main
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