from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import uvicorn
import os

# Import database
from database import get_db

# Import configuration
from core.config import settings
from core.limiter import limiter
from core.thread_pool import (
    shutdown_thread_pools,
    get_speech_thread_pool,
    get_audio_thread_pool,
    get_thread_pool_stats,
)

# Import middleware
# from middleware.rate_limiter import RateLimitMiddleware  # Temporarily disabled due to bug
from middleware.global_rate_limiter import global_rate_limiter

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
    admin_subscriptions,
    admin_monitoring,
    admin_billing,
    admin_audio_errors,
    teacher_review,
    subscription,
    payment,
    cron,
)
from routes import logs
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
elif environment == "develop":
    # Develop 環境允許所有來源（測試用）
    allowed_origins = ["*"]
elif environment == "staging":
    # Staging 環境暫時允許所有來源（方便測試）
    allowed_origins = ["*"]
elif environment == "preview":
    # Preview 環境（Per-Issue Test Environment）允許所有來源
    allowed_origins = ["*"]
elif environment == "production":
    # 生產環境只允許生產域名
    allowed_origins = [
        "https://duotopia.co",  # 主要自定義域名
        "https://duotopia.net",  # 備用自定義域名
        # Production Cloud Run (短網址)
        "https://duotopia-production-frontend-b2ovkkgl6a-de.a.run.app",
        # Production Cloud Run (完整網址)
        "https://duotopia-production-frontend-316409492201.asia-east1.run.app",
        "https://duotopia-469413.web.app",  # Firebase hosting (備用)
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


# 🔐 全局 Rate Limiting (补充 slowapi)
# 保守配置：500 请求/分钟 (观察 1 周后调整为 200)


@app.middleware("http")
async def global_rate_limit_middleware(request: Request, call_next):
    """
    全局速率限制 middleware

    目的：防止异常高频请求（如 2025-12-03 的 OOM 事件）
    配置：500 请求/分钟（非常宽松，正常用户不会触发）
    跳过：健康检查、静态文件
    """
    # 跳过健康检查和静态资源
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    if request.url.path.startswith("/static"):
        return await call_next(request)

    # 检查速率限制
    allowed, info = await global_rate_limiter.check_rate_limit(
        request,
        max_requests=500,  # 非常宽松（观察期）
        window_seconds=60,
    )

    if not allowed:
        # 返回 429 Too Many Requests
        return JSONResponse(
            status_code=429,
            content=info,
            headers={
                "Retry-After": str(info["retry_after"]),
                "X-RateLimit-Limit": str(info["limit"]),
            },
        )

    # 继续处理请求
    response = await call_next(request)

    # 添加 Rate Limit 信息到响应头（供调试）
    response.headers["X-RateLimit-Limit"] = str(info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])

    return response


# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# GCS is used for all file storage - no local storage needed


@app.on_event("startup")
async def startup_event():
    """應用程式啟動時初始化資源"""
    # 初始化線程池
    get_speech_thread_pool()
    get_audio_thread_pool()

    # 啟動全局 Rate Limiter 清理任務
    global_rate_limiter.start_cleanup_task()

    print("🚀 Application startup complete - Thread pools and rate limiter initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """應用程式關閉時清理資源"""
    # 關閉線程池
    shutdown_thread_pools(wait=True)
    print("👋 Application shutdown complete - Thread pools closed")


@app.get("/")
async def root():
    return {"message": "Duotopia API is running", "version": "1.0.1"}


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """健康檢查端點 - 檢查服務和資料庫狀態

    Performance optimization (Issue #96):
    - Uses connection pool via dependency injection
    - Added 2-second timeout to prevent hanging
    - Eliminates overhead of creating new connections
    """
    from sqlalchemy import text
    import time

    db_status = "unknown"
    db_latency = None

    try:
        # 測試資料庫連線（使用連接池 + 超時）
        start = time.time()
        statement = text("SELECT 1").execution_options(timeout=2)
        db.execute(statement)
        db_latency = round((time.time() - start) * 1000, 2)  # ms
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "duotopia-backend",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": {
            "status": db_status,
            "latency_ms": db_latency,
            "info": settings.get_database_info(),
        },
        "thread_pools": get_thread_pool_stats(),
    }


# 新增 /api/health 作為別名（符合 API 慣例）
@app.get("/api/health")
async def api_health_check():
    """API 健康檢查端點（/api/health 別名）"""
    return await health_check()


# Include routers
app.include_router(public.router)  # 公開路由優先，不需要認證
app.include_router(logs.router)  # 日誌路由（無需認證）
app.include_router(auth.router)
app.include_router(subscription.router)  # 訂閱路由
app.include_router(payment.router, prefix="/api", tags=["payment"])  # 金流路由

# 測試路由 - 僅在開發和 Staging 環境啟用
if environment in ["development", "staging"]:
    try:
        from tests.integration.api import test_subscription

        app.include_router(test_subscription.router)  # 測試訂閱路由（模擬充值，不經過 TapPay）
    except ImportError:
        # Production 環境沒有 tests 目錄，忽略錯誤
        pass
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(assignments.router)
app.include_router(unassign.router)
app.include_router(files.router)  # 檔案服務路由
app.include_router(programs.router)  # 課程管理路由
app.include_router(speech_assessment.router)  # 語音評估路由
app.include_router(teacher_review.router)  # 老師批改路由
app.include_router(admin.router)  # 管理路由
app.include_router(admin_subscriptions.router)  # Admin 訂閱管理路由（新）
app.include_router(admin_monitoring.router)  # 監控路由（無需認證）
app.include_router(admin_billing.router)  # Admin 帳單監控路由（Admin only）
app.include_router(admin_audio_errors.router)  # Admin 錄音錯誤監控路由（Admin only）
app.include_router(cron.router)  # Cron Job 路由
app.include_router(debug.router)  # Debug 路由


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
