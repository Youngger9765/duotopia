from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Import configuration
from core.config import settings

# Import routers
from routers import auth, students, teachers, public, assignments, unassign, files

app = FastAPI(
    title="Duotopia API",
    version="1.0.0",
    description=f"Running on {settings.deployment_name}",
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 暫時允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
