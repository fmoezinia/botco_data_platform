"""
AWS S3 service for cloud storage operations.
"""
import os
import logging
from typing import Optional, BinaryIO, List
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for AWS S3 operations."""
    
    def __init__(self):
        """Initialize S3 service."""
        self.s3_client = None
        self.bucket_name = settings.s3_bucket_name
        
        if settings.storage_mode == "s3" and self.bucket_name:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )
                logger.info(f"S3 service initialized for bucket: {self.bucket_name}")
            except NoCredentialsError:
                logger.error("AWS credentials not found")
                self.s3_client = None
            except Exception as e:
                logger.error(f"Failed to initialize S3 service: {e}")
                self.s3_client = None
    
    def is_available(self) -> bool:
        """Check if S3 service is available."""
        return self.s3_client is not None and self.bucket_name is not None
    
    def upload_file(self, local_file_path: str, s3_key: str) -> bool:
        """
        Upload a file to S3.
        
        Args:
            local_file_path: Path to local file
            s3_key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.warning("S3 service not available")
            return False
        
        try:
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            logger.info(f"Uploaded {local_file_path} to s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            return False
    
    def download_file(self, s3_key: str, local_file_path: str) -> bool:
        """
        Download a file from S3.
        
        Args:
            s3_key: S3 object key
            local_file_path: Path to save downloaded file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.warning("S3 service not available")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            self.s3_client.download_file(self.bucket_name, s3_key, local_file_path)
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_file_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {e}")
            return False
    
    def get_file_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for a file.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if failed
        """
        if not self.is_available():
            logger.warning("S3 service not available")
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in S3 bucket with given prefix.
        
        Args:
            prefix: S3 key prefix
            
        Returns:
            List of S3 keys
        """
        if not self.is_available():
            logger.warning("S3 service not available")
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
            
            logger.info(f"Listed {len(files)} files with prefix: {prefix}")
            return files
        except ClientError as e:
            logger.error(f"Failed to list S3 files: {e}")
            return []
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.warning("S3 service not available")
            return False
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete S3 file: {e}")
            return False
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False


# Global S3 service instance
s3_service = S3Service()
