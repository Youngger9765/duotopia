"""
Admin monitoring endpoints for audio upload and AI analysis status.
No authentication required for monitoring purposes.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin-monitoring"])

# Mock data storage (in production, this would come from database)
monitoring_stats = {
    "audio_uploads": {"total": 0, "successful": 0, "failed": 0, "retries": 0},
    "ai_analyses": {"total": 0, "successful": 0, "failed": 0, "retries": 0},
    "error_logs": [],
}


@router.get("/audio-upload-status")
async def get_audio_upload_status() -> Dict[str, Any]:
    """Get current audio upload status and statistics."""
    # Generate mock data with some randomness for demo
    base_uploads = monitoring_stats["audio_uploads"]["total"] or random.randint(
        100, 200
    )
    successful = int(base_uploads * random.uniform(0.85, 0.95))
    failed = base_uploads - successful

    return {
        "total_uploads": base_uploads,
        "successful": successful,
        "failed": failed,
        "in_progress": random.randint(0, 3),
        "retry_count": monitoring_stats["audio_uploads"]["retries"],
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/ai-analysis-status")
async def get_ai_analysis_status() -> Dict[str, Any]:
    """Get current AI analysis status and statistics."""
    # Generate mock data
    base_analyses = monitoring_stats["ai_analyses"]["total"] or random.randint(80, 150)
    successful = int(base_analyses * random.uniform(0.88, 0.98))
    failed = base_analyses - successful

    return {
        "total_analyses": base_analyses,
        "successful": successful,
        "failed": failed,
        "in_queue": random.randint(0, 5),
        "avg_processing_time": round(random.uniform(1.5, 3.5), 2),
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/retry-statistics")
async def get_retry_statistics() -> Dict[str, Any]:
    """Get retry statistics for both audio upload and AI analysis."""
    audio_retries = monitoring_stats["audio_uploads"]["retries"] or random.randint(
        10, 30
    )
    ai_retries = monitoring_stats["ai_analyses"]["retries"] or random.randint(5, 20)

    return {
        "audio_upload": {
            "total_retries": audio_retries,
            "successful_after_retry": int(audio_retries * 0.8),
            "failed_after_retry": int(audio_retries * 0.2),
            "retry_distribution": {
                "1": int(audio_retries * 0.6),
                "2": int(audio_retries * 0.3),
                "3": int(audio_retries * 0.1),
            },
        },
        "ai_analysis": {
            "total_retries": ai_retries,
            "successful_after_retry": int(ai_retries * 0.85),
            "failed_after_retry": int(ai_retries * 0.15),
            "retry_distribution": {
                "1": int(ai_retries * 0.65),
                "2": int(ai_retries * 0.25),
                "3": int(ai_retries * 0.1),
            },
        },
    }


@router.get("/error-logs")
async def get_error_logs(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent error logs."""
    # Return stored error logs or generate mock data
    if monitoring_stats["error_logs"]:
        return monitoring_stats["error_logs"][:limit]

    # Generate mock error logs
    error_types = [
        ("NetworkError: Failed to fetch", "audio_upload"),
        ("500 Internal Server Error", "audio_upload"),
        ("429 Too Many Requests", "ai_analysis"),
        ("503 Service Unavailable", "ai_analysis"),
        ("TimeoutError", "audio_upload"),
        ("ECONNRESET", "ai_analysis"),
    ]

    logs = []
    for i in range(min(limit, 5)):
        error_msg, error_type = random.choice(error_types)
        logs.append(
            {
                "id": i + 1,
                "timestamp": (
                    datetime.now() - timedelta(minutes=random.randint(1, 60))
                ).isoformat(),
                "type": error_type,
                "error": error_msg,
                "retry_count": random.randint(1, 3),
                "resolved": random.choice([True, False]),
            }
        )

    return logs


@router.post("/test-audio-upload")
async def test_audio_upload(
    audio_file: UploadFile = File(...), test_mode: Optional[str] = None
) -> Dict[str, Any]:
    """Test audio upload with retry mechanism."""
    try:
        # Update stats
        monitoring_stats["audio_uploads"]["total"] += 1

        # Simulate random success/failure for testing
        if test_mode and random.random() < 0.8:
            monitoring_stats["audio_uploads"]["successful"] += 1
            return {
                "success": True,
                "audio_url": f"https://storage.googleapis.com/test/audio_{datetime.now().timestamp()}.webm",
                "message": "測試上傳成功",
            }
        else:
            # Simulate retry scenario
            monitoring_stats["audio_uploads"]["retries"] += 1
            if random.random() < 0.7:  # 70% success after retry
                monitoring_stats["audio_uploads"]["successful"] += 1
                return {
                    "success": True,
                    "audio_url": f"https://storage.googleapis.com/test/audio_{datetime.now().timestamp()}.webm",
                    "message": "測試上傳成功（經重試）",
                }
            else:
                monitoring_stats["audio_uploads"]["failed"] += 1
                raise HTTPException(status_code=500, detail="測試上傳失敗")
    except Exception as e:
        logger.error(f"Test audio upload failed: {e}")
        monitoring_stats["audio_uploads"]["failed"] += 1

        # Log the error
        monitoring_stats["error_logs"].insert(
            0,
            {
                "id": len(monitoring_stats["error_logs"]) + 1,
                "timestamp": datetime.now().isoformat(),
                "type": "audio_upload",
                "error": str(e),
                "retry_count": 1,
                "resolved": False,
            },
        )

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-ai-analysis")
async def test_ai_analysis(
    test_text: str = "Hello world", test_mode: bool = True
) -> Dict[str, Any]:
    """Test AI analysis with retry mechanism."""
    try:
        # Update stats
        monitoring_stats["ai_analyses"]["total"] += 1

        # Simulate random success/failure for testing
        if test_mode and random.random() < 0.85:
            monitoring_stats["ai_analyses"]["successful"] += 1
            return {
                "success": True,
                "overall_score": random.randint(70, 95),
                "accuracy_score": random.randint(75, 98),
                "fluency_score": random.randint(70, 95),
                "pronunciation_score": random.randint(65, 90),
                "message": "AI 分析測試成功",
            }
        else:
            # Simulate retry scenario
            monitoring_stats["ai_analyses"]["retries"] += 1
            if random.random() < 0.75:  # 75% success after retry
                monitoring_stats["ai_analyses"]["successful"] += 1
                return {
                    "success": True,
                    "overall_score": random.randint(70, 95),
                    "message": "AI 分析測試成功（經重試）",
                }
            else:
                monitoring_stats["ai_analyses"]["failed"] += 1
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except Exception as e:
        logger.error(f"Test AI analysis failed: {e}")
        monitoring_stats["ai_analyses"]["failed"] += 1

        # Log the error
        monitoring_stats["error_logs"].insert(
            0,
            {
                "id": len(monitoring_stats["error_logs"]) + 1,
                "timestamp": datetime.now().isoformat(),
                "type": "ai_analysis",
                "error": str(e),
                "retry_count": 1,
                "resolved": False,
            },
        )

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-stats")
async def update_monitoring_stats(
    stat_type: str, action: str, count: int = 1
) -> Dict[str, str]:
    """
    Update monitoring statistics.
    This endpoint is called by the actual upload/analysis endpoints to track stats.
    """
    if stat_type == "audio_upload":
        if action == "success":
            monitoring_stats["audio_uploads"]["successful"] += count
            monitoring_stats["audio_uploads"]["total"] += count
        elif action == "failure":
            monitoring_stats["audio_uploads"]["failed"] += count
            monitoring_stats["audio_uploads"]["total"] += count
        elif action == "retry":
            monitoring_stats["audio_uploads"]["retries"] += count
    elif stat_type == "ai_analysis":
        if action == "success":
            monitoring_stats["ai_analyses"]["successful"] += count
            monitoring_stats["ai_analyses"]["total"] += count
        elif action == "failure":
            monitoring_stats["ai_analyses"]["failed"] += count
            monitoring_stats["ai_analyses"]["total"] += count
        elif action == "retry":
            monitoring_stats["ai_analyses"]["retries"] += count

    return {"status": "updated"}


@router.get("/health-check")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "admin-monitoring",
    }
