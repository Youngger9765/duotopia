from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import uvicorn
import os

# Import configuration
from core.config import settings
from core.limiter import limiter

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
    admin_monitoring,
    teacher_review,
    subscription,
    payment,
)
from api import debug

app = FastAPI(
    title="Duotopia API",
    version="1.0.0",
    description=f"Running on {settings.deployment_name}",
)

# 🔐 Rate Limiting - slowapi for auth endpoints
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
        "https://duotopia.net",  # 自定義域名
        "https://duotopia.co",  # 自定義域名
        "https://duotopia-production-frontend-316409492201.asia-east1.run.app",  # Production Cloud Run frontend
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

# GCS is used for all file storage - no local storage needed


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
app.include_router(subscription.router)  # 訂閱路由
app.include_router(payment.router, prefix="/api", tags=["payment"])  # 金流路由
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(assignments.router)
app.include_router(unassign.router)
app.include_router(files.router)  # 檔案服務路由
app.include_router(programs.router)  # 課程管理路由
app.include_router(speech_assessment.router)  # 語音評估路由
app.include_router(teacher_review.router)  # 老師批改路由
app.include_router(admin.router)  # 管理路由
app.include_router(admin_monitoring.router)  # 監控路由（無需認證）
app.include_router(debug.router)  # Debug 路由


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
