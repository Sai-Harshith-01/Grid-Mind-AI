"""Pydantic schemas for health and app metadata endpoints."""

from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check payload response schema."""
    status: str = Field(default="ok", description="Overall service operational health")
    service: str = Field(..., description="Service identifier")
    version: str = Field(..., description="Deployed semantic version")
    timestamp: datetime = Field(..., description="Server timestamp of check in UTC")


class AppInfoResponse(BaseModel):
    """Application metadata root response schema."""
    name: str = Field(..., description="Application name")
    description: str = Field(..., description="Short platform overview")
    version: str = Field(..., description="Application version")
    docs_url: str = Field(..., description="OpenAPI interactive documentation path")
