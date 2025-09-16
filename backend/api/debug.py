"""Debug endpoints for system testing"""
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/system-check")
async def system_check():
    """Check system configuration and environment variables"""

    # Check Azure Speech Service configuration
    azure_config = {
        "speech_key_exists": bool(os.getenv("AZURE_SPEECH_KEY")),
        "speech_region": os.getenv("AZURE_SPEECH_REGION", "Not set"),
        "speech_endpoint": os.getenv("AZURE_SPEECH_ENDPOINT", "Not set"),
    }

    # Check Google Cloud Storage configuration
    gcs_config = {
        "bucket_name": os.getenv("GCS_BUCKET_NAME", "Not set"),
        "credentials_exist": bool(os.getenv("GCS_SERVICE_ACCOUNT_KEY")),
        "project_id": os.getenv("GCP_PROJECT_ID", "Not set"),
    }

    # Check database configuration
    db_config = {
        "database_url_exists": bool(os.getenv("DATABASE_URL")),
        "db_host": os.getenv("DB_HOST", "Not set"),
        "db_name": os.getenv("DB_NAME", "Not set"),
    }

    # Check general configuration
    general_config = {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
        "cors_origins": os.getenv("CORS_ORIGINS", "Not set"),
    }

    return JSONResponse(
        content={
            "status": "ok",
            "azure": azure_config,
            "gcs": gcs_config,
            "database": db_config,
            "general": general_config,
            "message": "System check completed",
        },
        status_code=200,
    )


@router.get("/health")
async def debug_health():
    """Simple health check for debug purposes"""
    return {
        "status": "healthy",
        "service": "debug",
        "timestamp": os.popen("date").read().strip(),
    }
