from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

# Import configuration
from core.config import settings

# Import middleware
# from middleware.rate_limiter import RateLimitMiddleware  # Temporarily disabled due to bug

# Import routers
from routers import (
    auth,
    students,
    teachers,
    public,
    assignments,
    unassign,
    files,
    programs,
    speech_assessment,
    admin,
)

app = FastAPI(
    title="Duotopia API",
    version="1.0.0",
    description=f"Running on {settings.deployment_name}",
)

# Rate Limiting 設定 - Temporarily disabled due to middleware bug
# redis_url = os.getenv("REDIS_URL", None)  # 如果有 Redis 就用，沒有就用記憶體
# app.add_middleware(RateLimitMiddleware, redis_url=redis_url)

# CORS 設定
environment = os.getenv("ENVIRONMENT", "development")

if environment == "development":
    # 開發環境可以使用較寬鬆的設定
    allowed_origins = ["*"]
elif environment == "staging":
    # Staging 環境暫時允許所有來源（方便測試）
    allowed_origins = ["*"]
elif environment == "production":
    # 生產環境只允許生產域名
    allowed_origins = [
        "https://duotopia-469413.web.app",
        "https://duotopia.com",  # 如果有自定義域名
    ]
else:
    # 其他環境使用環境變數或預設值
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(
        ","
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    return {"message": "Duotopia API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "duotopia-backend",
        "database": settings.get_database_info(),
    }


# Include routers
app.include_router(public.router)  # 公開路由優先，不需要認證
app.include_router(auth.router)
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(assignments.router)
app.include_router(unassign.router)
app.include_router(files.router)  # 檔案服務路由
app.include_router(programs.router)  # 課程管理路由
app.include_router(speech_assessment.router)  # 語音評估路由
app.include_router(admin.router)  # 管理路由


# 臨時 debug endpoint
@app.get("/api/debug/system-check")
async def system_check():
    """臨時端點：檢查系統環境"""
    import subprocess

    checks = {}

    # 檢查 ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        checks["ffmpeg"] = "installed" if result.returncode == 0 else "not found"
        checks["ffmpeg_version"] = (
            result.stdout.split("\n")[0] if result.returncode == 0 else None
        )
    except Exception as e:
        checks["ffmpeg"] = f"error: {str(e)}"

    # 檢查 Azure 環境變數
    checks["azure_key_exists"] = bool(os.getenv("AZURE_SPEECH_KEY"))
    checks["azure_region"] = os.getenv("AZURE_SPEECH_REGION", "Not set")

    return checks


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
