"""Core configuration module for GridMind AI backend."""

from typing import List, Optional
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


class Settings(BaseModel):
    PROJECT_NAME: str = Field(default="GridMind AI")
    DESCRIPTION: str = Field(
        default="AI-powered renewable energy intelligence and optimisation platform for MSME factories."
    )
    VERSION: str = Field(default="0.1.0")
    ENVIRONMENT: str = Field(default=os.getenv("ENVIRONMENT", "development"))
    HOST: str = Field(default=os.getenv("HOST", "0.0.0.0"))
    PORT: int = Field(default=int(os.getenv("PORT", "8000")))

    # CORS configuration
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
            ).split(",")
            if origin.strip()
        ]
    )

    # Google Gemini AI settings
    GEMINI_API_KEY: Optional[str] = Field(default=os.getenv("GEMINI_API_KEY"))
    GEMINI_MODEL: str = Field(default=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"))
    GEMINI_REQUEST_TIMEOUT_SECONDS: int = Field(
        default=int(os.getenv("GEMINI_REQUEST_TIMEOUT_SECONDS", "30"))
    )
    GEMINI_MAX_RETRIES: int = Field(
        default=int(os.getenv("GEMINI_MAX_RETRIES", "2"))
    )
    INVESTIGATION_MAX_FINDINGS_PER_REPORT: int = Field(
        default=int(os.getenv("INVESTIGATION_MAX_FINDINGS_PER_REPORT", "5"))
    )


settings = Settings()
