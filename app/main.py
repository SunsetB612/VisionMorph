# FastAPI应用入口
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.modules.crop.api import router as crop_router
from app.modules.upload.api import router as upload_router
from app.modules.generate.api import router as generate_router
from app.modules.score.api import router as score_router
from app.modules.result.api import router as result_router
from app.modules.user.api import router as user_router
import os

# 创建FastAPI应用实例
app = FastAPI(
    title="VisionMorph API",
    description="智能构图生成系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册API路由
app.include_router(user_router, prefix="/api/auth", tags=["auth"])
app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(crop_router, prefix="/api", tags=["crop"])
app.include_router(generate_router, prefix="/api", tags=["generate"])
app.include_router(score_router, prefix="/api", tags=["score"])
app.include_router(result_router, prefix="/api", tags=["result"])

@app.get("/")
async def root():
    return {"message": "VisionMorph API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "VisionMorph"}

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
