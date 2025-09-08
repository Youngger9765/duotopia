"""
Configuration for multi-database support
Supports switching between Supabase and Cloud SQL
"""

import os
from typing import Literal, Optional  # noqa: F401
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
# 環境優先順序：.env.local > .env.staging > .env
root_dir = Path(__file__).parent.parent.parent

# 先嘗試載入 .env.local（本地開發）
env_local = root_dir / ".env.local"
env_staging = root_dir / ".env.staging"
env_default = root_dir / ".env"

# Silent loading - no console output for security
if env_local.exists():
    load_dotenv(env_local, override=True)
elif env_staging.exists() and os.getenv("ENVIRONMENT") == "staging":
    load_dotenv(env_staging, override=True)
elif env_default.exists():
    load_dotenv(env_default, override=True)
else:
    load_dotenv()


class Settings:
    # Environment
    ENVIRONMENT: Literal["local", "staging", "production"] = os.getenv(
        "ENVIRONMENT", "local"
    )
    DATABASE_TYPE: Literal["local", "supabase", "cloudsql"] = os.getenv(
        "DATABASE_TYPE", "local"
    )

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia",
    )

    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

    # Supabase (optional)
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

    # Google OAuth (optional)
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")

    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Azure Speech Services (optional)
    AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION: Optional[str] = os.getenv("AZURE_SPEECH_REGION", "eastasia")
    AZURE_SPEECH_ENDPOINT: Optional[str] = os.getenv("AZURE_SPEECH_ENDPOINT")

    # GCP (optional)
    GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID", "duotopia-469413")

    @property
    def deployment_name(self) -> str:
        """Get deployment name for logging"""
        return f"{self.ENVIRONMENT}-{self.DATABASE_TYPE}"

    @property
    def is_free_tier(self) -> bool:
        """Check if using free tier database"""
        return self.DATABASE_TYPE == "supabase" or self.DATABASE_TYPE == "local"

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.ENVIRONMENT == "staging"

    @property
    def is_local(self) -> bool:
        """Check if running locally"""
        return self.ENVIRONMENT == "local"

    def get_cost_per_day(self) -> float:
        """Get estimated daily cost in USD"""
        if self.DATABASE_TYPE == "cloudsql":
            return 2.28  # Cloud SQL with public IP
        return 0.0  # Supabase or local

    def get_database_info(self) -> dict:
        """Get database information for health checks"""
        return {
            "type": self.DATABASE_TYPE,
            "environment": self.ENVIRONMENT,
            "deployment": self.deployment_name,
            "is_free_tier": self.is_free_tier,
            "daily_cost_usd": self.get_cost_per_day(),
        }

    def validate(self):
        """Validate configuration"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")

        if self.DATABASE_TYPE == "supabase" and not self.SUPABASE_URL:
            # Silent warning - don't expose configuration details
            pass

        if (
            self.is_production
            and self.JWT_SECRET == "your-secret-key-change-in-production"
        ):
            raise ValueError("Please set a secure JWT_SECRET for production")

        return True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.validate()
    return settings


# Export for convenience
settings = get_settings()
