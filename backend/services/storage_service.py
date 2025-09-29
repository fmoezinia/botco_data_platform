"""
Storage service abstraction for local and cloud storage.
"""
import os
import logging
from typing import Optional, List, BinaryIO
from pathlib import Path
from abc import ABC, abstractmethod

from config import settings
from services.s3_service import s3_service

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Abstract base class for storage services."""
    
    @abstractmethod
    def save_file(self, file_path: str, content: bytes) -> bool:
        """Save file content to storage."""
        pass
    
    @abstractmethod
    def get_file_url(self, file_path: str) -> Optional[str]:
        """Get URL to access file."""
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage."""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """List files with given prefix."""
        pass


class LocalStorageService(StorageService):
    """Local file system storage service."""
    
    def __init__(self, base_dir: str = "data"):
        """Initialize local storage service."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        logger.info(f"Local storage initialized at: {self.base_dir.absolute()}")
    
    def save_file(self, file_path: str, content: bytes) -> bool:
        """Save file content to local storage."""
        try:
            full_path = self.base_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Saved file to local storage: {full_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save file to local storage: {e}")
            return False
    
    def get_file_url(self, file_path: str) -> Optional[str]:
        """Get local file URL."""
        full_path = self.base_dir / file_path
        if full_path.exists():
            return f"/static/{file_path}"
        return None
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage."""
        return (self.base_dir / file_path).exists()
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage."""
        try:
            full_path = self.base_dir / file_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file from local storage: {full_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file from local storage: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """List files with given prefix in local storage."""
        try:
            prefix_path = self.base_dir / prefix
            files = []
            
            if prefix_path.exists():
                for file_path in prefix_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(self.base_dir)
                        files.append(str(relative_path))
            
            logger.info(f"Listed {len(files)} files with prefix: {prefix}")
            return files
        except Exception as e:
            logger.error(f"Failed to list local files: {e}")
            return []


class S3StorageService(StorageService):
    """S3 cloud storage service."""
    
    def __init__(self, prefix: str = ""):
        """Initialize S3 storage service."""
        self.prefix = prefix
        self.s3_service = s3_service
        logger.info(f"S3 storage initialized with prefix: {prefix}")
    
    def save_file(self, file_path: str, content: bytes) -> bool:
        """Save file content to S3."""
        s3_key = f"{self.prefix}{file_path}"
        
        # First save to local temp file, then upload
        temp_path = f"/tmp/{file_path}"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        try:
            with open(temp_path, 'wb') as f:
                f.write(content)
            
            success = self.s3_service.upload_file(temp_path, s3_key)
            os.remove(temp_path)  # Clean up temp file
            return success
        except Exception as e:
            logger.error(f"Failed to save file to S3: {e}")
            return False
    
    def get_file_url(self, file_path: str) -> Optional[str]:
        """Get S3 file URL."""
        s3_key = f"{self.prefix}{file_path}"
        return self.s3_service.get_file_url(s3_key)
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3."""
        s3_key = f"{self.prefix}{file_path}"
        return self.s3_service.file_exists(s3_key)
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from S3."""
        s3_key = f"{self.prefix}{file_path}"
        return self.s3_service.delete_file(s3_key)
    
    def list_files(self, prefix: str = "") -> List[str]:
        """List files with given prefix in S3."""
        full_prefix = f"{self.prefix}{prefix}"
        files = self.s3_service.list_files(full_prefix)
        # Remove the service prefix from returned file paths
        return [f[len(self.prefix):] for f in files if f.startswith(self.prefix)]


class StorageManager:
    """Storage manager that handles both local and cloud storage."""
    
    def __init__(self):
        """Initialize storage manager."""
        self.local_storage = LocalStorageService(settings.data_dir)
        
        if settings.storage_mode == "s3":
            self.video_storage = S3StorageService(settings.s3_videos_prefix)
            self.visualization_storage = S3StorageService(settings.s3_visualizations_prefix)
        else:
            self.video_storage = LocalStorageService(f"{settings.data_dir}/videos")
            self.visualization_storage = LocalStorageService(f"{settings.data_dir}/visualizations")
        
        logger.info(f"Storage manager initialized with mode: {settings.storage_mode}")
    
    def get_video_url(self, video_path: str) -> Optional[str]:
        """Get URL for video file."""
        return self.video_storage.get_file_url(video_path)
    
    def get_visualization_url(self, viz_path: str) -> Optional[str]:
        """Get URL for visualization file."""
        return self.visualization_storage.get_file_url(viz_path)
    
    def save_visualization(self, viz_path: str, content: bytes) -> bool:
        """Save visualization file."""
        return self.visualization_storage.save_file(viz_path, content)
    
    def video_exists(self, video_path: str) -> bool:
        """Check if video file exists."""
        return self.video_storage.file_exists(video_path)
    
    def visualization_exists(self, viz_path: str) -> bool:
        """Check if visualization file exists."""
        return self.visualization_storage.file_exists(viz_path)


# Global storage manager instance
storage_manager = StorageManager()
