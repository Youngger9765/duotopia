from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Security
    jwt_secret: Optional[str] = None
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Google Cloud
    gcp_project_id: str = "duotopia-469413"
    gcs_bucket_name: str = "duotopia-uploads"
    
    # Email
    sendgrid_api_key: Optional[str] = None
    from_email: str = "noreply@duotopia.com"
    
    # CORS
    backend_cors_origins: list = [
        "http://localhost:5173", 
        "http://localhost:5174",
        "https://duotopia-frontend-staging-206313737181.asia-east1.run.app"
    ]
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use JWT_SECRET if secret_key is not set
        if not self.secret_key:
            self.secret_key = self.jwt_secret or os.getenv("JWT_SECRET")
        # Validate critical settings
        if not self.secret_key:
            raise ValueError("JWT_SECRET must be set to a secure value")
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set")

settings = Settings()