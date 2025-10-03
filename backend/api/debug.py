"""Debug endpoints for system testing"""
import os
from fastapi import APIRouter, UploadFile, File, Form
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


@router.post("/test-upload")
async def test_upload_no_auth(
    file: UploadFile = File(...),
    duration_seconds: int = Form(5),
):
    """測試音檔上傳 (無認證版本)"""
    try:
        import uuid
        from datetime import datetime

        # 讀取檔案內容
        content = await file.read()

        # 檢查檔案大小
        max_size = 2 * 1024 * 1024  # 2MB
        if len(content) > max_size:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "File too large"},
            )

        # 檢查檔案類型
        allowed_types = [
            "audio/webm",
            "audio/webm;codecs=opus",
            "audio/mp3",
            "audio/wav",
            "audio/mpeg",
            "audio/wave",
            "application/octet-stream",  # 瀏覽器上傳時的通用類型
        ]
        if file.content_type not in allowed_types:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"Invalid file type: {file.content_type}",
                },
            )

        # 生成檔名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = str(uuid.uuid4())[:8]
        filename = f"debug_upload_{timestamp}_{file_id}_{file.filename}"

        # 儲存到本地
        local_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "local_recordings"
        )
        os.makedirs(local_dir, exist_ok=True)

        local_path = os.path.join(local_dir, filename)
        with open(local_path, "wb") as f:
            f.write(content)

        return {
            "status": "success",
            "message": "Upload successful (no auth)",
            "audio_url": f"/local_recordings/{filename}",
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "local_path": local_path,
            },
        }

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


@router.post("/test-azure-speech")
async def test_azure_speech_no_auth(
    file: UploadFile = File(...),
    reference_text: str = Form("Hello world"),
):
    """測試 Azure Speech Assessment (無認證版本)"""
    try:
        import tempfile

        # 保存臨時檔案
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # 這裡可以加入 Azure Speech SDK 測試
            # 現在先返回模擬結果
            return {
                "status": "success",
                "message": "Azure Speech test (no auth)",
                "assessment": {
                    "reference_text": reference_text,
                    "pronunciation_score": 85.5,
                    "accuracy_score": 90.2,
                    "fluency_score": 78.9,
                    "completeness_score": 95.0,
                    "mock": True,
                },
                "file_info": {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(content),
                },
            }
        finally:
            # 清理臨時檔案
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


@router.post("/test-gcs-simple")
async def test_gcs_simple_no_auth(
    file: UploadFile = File(...),
):
    """測試 GCS 上傳 (無認證簡化版本)"""
    try:
        content = await file.read()

        # 模擬 GCS 上傳流程
        result = {
            "status": "success",
            "message": "GCS test completed (no auth)",
            "simulation": {
                "would_upload_to": "duotopia-audio/recordings/",
                "file_size": len(content),
                "content_type": file.content_type,
                "filename": file.filename,
                "mock_url": f"https://storage.googleapis.com/duotopia-audio/recordings/mock_{file.filename}",
            },
        }

        # 在本地開發環境，實際儲存到本地
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "development":
            try:
                import uuid
                from datetime import datetime

                # 生成唯一檔名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_id = str(uuid.uuid4())[:8]
                local_filename = f"debug_test_{timestamp}_{file_id}_{file.filename}"

                # 確保目錄存在
                local_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "local_recordings"
                )
                os.makedirs(local_dir, exist_ok=True)

                # 儲存檔案
                local_path = os.path.join(local_dir, local_filename)
                with open(local_path, "wb") as f:
                    f.write(content)

                result["local_storage"] = {
                    "saved": True,
                    "path": local_path,
                    "url": f"/local_recordings/{local_filename}",
                }

            except Exception as local_error:
                result["local_storage"] = {"saved": False, "error": str(local_error)}

        return result

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )
