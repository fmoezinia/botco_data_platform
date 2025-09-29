"""
SAM2 AI service for video segmentation.
"""
import logging
import os
from typing import Dict, Any, Optional
import asyncio
import time

from config import settings
from utils.logging import logger
from exceptions import SAM2Error, ServiceUnavailableError
from models import TaskStatus, ProcessingResult, SegmentationResult, MaskData, ObjectTracking


class SAM2Service:
    """Service for SAM2 AI processing."""
    
    def __init__(self):
        """Initialize SAM2 service."""
        self.predictor = None
        self.model = None
        self.mask_generator = None
        self.device = None
        self.initialized = False
        self.mask_generator_available = False
        logger.info("SAM2 service initialized")
    
    async def initialize(self):
        """Initialize the SAM2 model."""
        try:
            logger.info("Loading SAM2 model...")
            
            # Check if SAM2 is installed
            try:
                from sam2.sam2_video_predictor import SAM2VideoPredictor
                from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
                import torch
            except ImportError as e:
                logger.warning(f"SAM2 not installed: {e}")
                logger.info("SAM2 service will be disabled")
                return
            
            # Determine device
            if settings.sam2_device == "auto":
                self.device = "cpu" if not torch.cuda.is_available() else "cuda"
            else:
                self.device = settings.sam2_device
            
            logger.info(f"Using device: {self.device}")
            
            # Load video predictor using the working method
            self.predictor = SAM2VideoPredictor.from_pretrained("facebook/sam2-hiera-tiny", device=self.device)
            self.model = self.predictor
            
            logger.info("SAM2 model loaded successfully")
            
            # Initialize automatic mask generator
            try:
                self.mask_generator = SAM2AutomaticMaskGenerator(
                    model=self.model,
                    points_per_side=32,
                    pred_iou_thresh=0.86,
                    stability_score_thresh=0.92,
                    crop_n_layers=1,
                    crop_n_points_downscale_factor=2,
                    min_mask_region_area=100,
                )
                logger.info("SAM2 automatic mask generator initialized successfully")
                self.mask_generator_available = True
            except Exception as e:
                logger.warning(f"Could not initialize automatic mask generator: {e}")
                self.mask_generator = None
                self.mask_generator_available = False
            
            self.initialized = True
            logger.info("SAM2 service initialized successfully")
            
        except Exception as e:
            logger.warning(f"SAM2 initialization failed: {e}")
            logger.info("SAM2 service will be disabled")
    
    def is_ready(self) -> bool:
        """Check if SAM2 service is ready."""
        return self.initialized and self.model is not None
    
    async def process_video(
        self, 
        video_path: str, 
        prompts: Optional[list] = None,
        mode: str = "automatic_mask_generator"
    ) -> ProcessingResult:
        """
        Process video with SAM2 segmentation.
        
        Args:
            video_path: Path to video file
            prompts: Optional prompts for segmentation
            mode: Processing mode
            
        Returns:
            ProcessingResult with segmentation data
        """
        if not self.is_ready():
            raise ServiceUnavailableError("SAM2 service not initialized")
        
        try:
            logger.info(f"Processing video: {video_path}")
            start_time = time.time()
            
            # Use the working logic from sam2hiera_service.py
            from sam2hiera_service import _sam2_video_processing_task
            
            # Create a simple progress callback function
            def progress_callback(progress: float):
                logger.info(f"Processing progress: {progress:.1%}")
            
            # Process video using the existing working implementation
            # Arguments: task_id, progress_callback, relative_video_path, prompts, mode
            result = _sam2_video_processing_task(
                task_id="sam2_task", 
                progress_callback=progress_callback, 
                relative_video_path=video_path, 
                prompts=prompts, 
                mode=mode
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Video processing completed in {processing_time:.2f} seconds")
            
            return ProcessingResult(
                video_path=video_path,
                total_frames=result.get('total_frames', 0),
                segmentation_results=result.get('segmentation_results', []),
                object_tracking=result.get('object_tracking', {}),
                processing_time=processing_time,
                note=f"Processed with {mode} mode"
            )
            
        except Exception as e:
            logger.error(f"SAM2 processing failed: {e}")
            raise SAM2Error(f"Video processing failed: {str(e)}")


# Global SAM2 service instance
sam2_service = SAM2Service()
