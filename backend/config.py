"""
Configuration management for the Botco Data Platform.
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="Botco Data Platform", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # CORS
    cors_origins: list = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    
    # Data paths
    data_dir: str = Field(default="data", env="DATA_DIR")
    videos_dir: str = Field(default="data/videos", env="VIDEOS_DIR")
    visualizations_dir: str = Field(default="data/visualizations", env="VISUALIZATIONS_DIR")
    
    # SAM2 AI
    sam2_model_name: str = Field(default="facebook/sam2-hiera-tiny", env="SAM2_MODEL_NAME")
    sam2_device: str = Field(default="auto", env="SAM2_DEVICE")  # auto, cpu, cuda
    
    # Task management
    task_timeout: float = Field(default=20.0, env="TASK_TIMEOUT")
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    
    # AWS S3 (for future cloud storage)
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    s3_bucket_name: Optional[str] = Field(default=None, env="S3_BUCKET_NAME")
    s3_videos_prefix: str = Field(default="videos/", env="S3_VIDEOS_PREFIX")
    s3_visualizations_prefix: str = Field(default="visualizations/", env="S3_VISUALIZATIONS_PREFIX")
    
    # Storage mode (local or s3)
    storage_mode: str = Field(default="local", env="STORAGE_MODE")  # local, s3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
