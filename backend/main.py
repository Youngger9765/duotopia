from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from database import engine, Base
from routers import auth, teachers, students

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Duotopia API server...")
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

@app.get("/")
async def root():
    return {"message": "Welcome to Duotopia API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}