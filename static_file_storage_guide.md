# 📁 Static 文件存储路径说明

## 📂 目录结构

```
static/
└── user{用户ID}/
    ├── original/      # 用户上传的原始图片
    ├── prompts/       # AI 生成的提示词文件
    ├── results/       # AI 生成的效果图
    ├── avatar/        # 用户头像（预留）
    └── temp/          # 临时文件（预留）
```

**示例**：
```
static/
└── user1/
    ├── original/
    │   └── user1_img_001_1698765432000.jpg
    ├── prompts/
    │   ├── user1_img_001_1698765432000_prompt_1.txt
    │   ├── user1_img_001_1698765432000_prompt_2.txt
    │   └── user1_img_001_1698765432000_prompt_3.txt
    └── results/
        ├── user1_img_001_1698765432000_generated_1.jpg
        ├── user1_img_001_1698765432000_generated_2.jpg
        └── user1_img_001_1698765432000_generated_3.jpg
```

---

## 📝 文件命名规范

### 1. 原始图片
```
格式：user{用户ID}_img_{序号}_{时间戳}.{扩展名}
示例：user1_img_001_1698765432000.jpg
位置：static/user{用户ID}/original/
```

### 2. Prompt 文件
```
格式：user{用户ID}_img_{序号}_{时间戳}_prompt_{索引}.txt
示例：user1_img_001_1698765432000_prompt_1.txt
位置：static/user{用户ID}/prompts/
```

### 3. 生成图片
```
格式：user{用户ID}_img_{序号}_{时间戳}_generated_{索引}.jpg
示例：user1_img_001_1698765432000_generated_1.jpg
位置：static/user{用户ID}/results/
```

---

## 🔗 文件关联逻辑

通过**文件名前缀**（`user{ID}_img_{序号}_{时间戳}`）实现关联：

```
原始图片：user1_img_001_1698765432000.jpg
         └─ 前缀：user1_img_001_1698765432000
            ├─ user1_img_001_1698765432000_prompt_1.txt
            ├─ user1_img_001_1698765432000_prompt_2.txt
            ├─ user1_img_001_1698765432000_generated_1.jpg
            └─ user1_img_001_1698765432000_generated_2.jpg
```

---

## 🎯 字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `{用户ID}` | 用户数据库 ID | `1` |
| `{序号}` | 上传的第几张图（3位数） | `001`, `002` |
| `{时间戳}` | 毫秒级时间戳（13位） | `1698765432000` |
| `{索引}` | Prompt/生成图编号 | `1`, `2`, `3` |
| `{扩展名}` | 文件格式 | `jpg`, `png` |


