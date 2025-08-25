from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from config import settings
from database import engine, Base
from routers import auth, teachers, students, admin, role_management, institutional, individual, student_login
from db_init import DatabaseInitializer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: Table creation is handled by alembic migrations

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Duotopia API server...")
    
    # Skip database initialization - handled by alembic migrations
    # try:
    #     with DatabaseInitializer() as db_init:
    #         db_init.initialize()
    # except Exception as e:
    #     logger.error(f"Failed to initialize database: {e}")
    #     # In production, we might want to exit here
    #     if os.getenv("ENVIRONMENT") == "production":
    #         raise
    
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Duotopia API",
    description="AI-powered English learning platform API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(admin.router)
app.include_router(role_management.router)
app.include_router(institutional.router)
app.include_router(individual.router)
app.include_router(student_login.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Duotopia API"}

@app.get("/health")
async def health_check():
    """Health check endpoint with database status"""
    from database import SessionLocal
    import models
    
    health_status = {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "unknown"
    }
    
    # Check database connectivity
    try:
        db = SessionLocal()
        # Simple query to verify database is accessible
        user_count = db.query(models.User).count()
        student_count = db.query(models.Student).count()
        
        health_status["database"] = "connected"
        health_status["data"] = {
            "users": user_count,
            "students": student_count
        }
        db.close()
    except Exception as e:
        health_status["database"] = "error"
        health_status["error"] = str(e)
        
    return health_status