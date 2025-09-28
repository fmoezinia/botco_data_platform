"""
SAM2-Hiera-Tiny model service for video processing.
"""
import time
import os
from typing import Dict, Any, Optional, List
import cv2
import numpy as np
import torch
from sam2.sam2_video_predictor import SAM2VideoPredictor
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
from task_manager import TaskStatus
from sam2visualizations import create_simple_visualization

# Configuration
VIDEO_BASE_DIR = "data/videos"

class Sam2HieraTinyModel:
    """SAM2-Hiera-Tiny model implementation."""
    
    def __init__(self):
        print("Loading SAM2-Hiera-Tiny model...")
        
        try:
            device = "cpu" if not torch.cuda.is_available() else "cuda"
            print(f"Using device: {device}")
            
            # Load video predictor
            self.predictor = SAM2VideoPredictor.from_pretrained("facebook/sam2-hiera-tiny", device=device)
            self.model = self.predictor
            
            print("SAM2-Hiera-Tiny model loaded successfully.")
            
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
                print("SAM2 automatic mask generator initialized successfully.")
                self.mask_generator_available = True
            except Exception as e:
                print(f"Warning: Could not initialize automatic mask generator: {e}")
                self.mask_generator = None
                self.mask_generator_available = False
            
            self.model_available = True
        except Exception as e:
            print(f"Error loading SAM2 model: {e}")
            self.predictor = None
            self.model = None
            self.mask_generator = None
            self.model_available = False
            self.mask_generator_available = False

    def process_video(self, video_path: str, prompts: List[Dict[str, Any]], mode: str = "automatic_mask_generator") -> Dict[str, Any]:
        """Process video with SAM2 model."""
        print(f"SAM2 processing: {video_path}, mode: {mode}")
        
        # Get video properties
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        print(f"Video: {frame_count_total} frames, {width}x{height}, {fps} FPS")
        
        # Check if model is available
        if not self.model_available:
            print("SAM2 model not available, using simulated processing...")
            return self._simulate_processing(video_path, frame_count_total, width, height)
        
        # Choose processing mode
        if mode == "automatic_mask_generator":
            return self._process_with_automatic_mask_generator(video_path, frame_count_total, width, height)
        elif mode == "video_predictor":
            return self._process_with_video_predictor(video_path, prompts, frame_count_total, width, height)
        else:
            raise ValueError(f"Unknown processing mode: {mode}")

    def _simulate_processing(self, video_path: str, frame_count_total: int, width: int, height: int) -> Dict[str, Any]:
        """Simulate processing for testing."""
        time.sleep(2)  # Simulate processing time
        
        segmentation_results = []
        for frame_idx in range(0, min(10, frame_count_total), 2):
            frame_results = {
                'frame_idx': frame_idx,
                'object_ids': [1, 2] if frame_idx % 4 == 0 else [1],
                'masks': [
                    np.zeros((height//4, width//4), dtype=bool).tolist(),
                    np.ones((height//4, width//4), dtype=bool).tolist()
                ] if frame_idx % 4 == 0 else [np.zeros((height//4, width//4), dtype=bool).tolist()],
                'timestamp': time.time()
            }
            segmentation_results.append(frame_results)
        
        return {
            'video_path': video_path,
            'total_frames': frame_count_total,
            'segmentation_results': segmentation_results,
            'object_tracking': {1: {'first_frame': 0, 'initial_mask': []}, 2: {'first_frame': 4, 'initial_mask': []}},
            'processing_time': time.time(),
            'note': 'Simulated processing'
        }

    def _process_with_automatic_mask_generator(self, video_path: str, frame_count_total: int, width: int, height: int) -> Dict[str, Any]:
        """Process video using SAM2 automatic mask generator."""
        print("Using SAM2 automatic mask generator...")
        
        # Convert MP4 path to JPEG folder path
        jpeg_folder_path = video_path.replace('.mp4', '')
        print(f"Looking for JPEG folder: {jpeg_folder_path}")
        
        if not os.path.exists(jpeg_folder_path):
            print("JPEG folder not found, falling back to simulated processing...")
            return self._simulate_processing(video_path, frame_count_total, width, height)
        
        if not self.mask_generator_available or self.mask_generator is None:
            print("Automatic mask generator not available, falling back to simulated processing...")
            return self._simulate_processing(video_path, frame_count_total, width, height)
        
        try:
            # Load first image from JPEG folder
            jpeg_files = [f for f in os.listdir(jpeg_folder_path) if f.endswith('.jpg')]
            jpeg_files.sort()
            
            if not jpeg_files:
                raise Exception(f"No JPEG files found in folder: {jpeg_folder_path}")
            
            first_image_path = os.path.join(jpeg_folder_path, jpeg_files[0])
            image = cv2.imread(first_image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            print(f"Loaded image with shape: {image.shape}")
            
            # Generate masks for the first frame
            masks = self.mask_generator.generate(image)
            print(f"Generated {len(masks)} masks")
            
            # Process all JPEG frames and apply masks to each
            segmentation_results = []
            object_tracking = {}
            
            # Process each JPEG frame
            for frame_idx, jpeg_file in enumerate(jpeg_files):
                if frame_idx >= len(jpeg_files):
                    break
                    
                frame_path = os.path.join(jpeg_folder_path, jpeg_file)
                frame_image = cv2.imread(frame_path)
                frame_image = cv2.cvtColor(frame_image, cv2.COLOR_BGR2RGB)
                
                # For now, use the same masks for all frames (we can improve this later)
                # In a more advanced implementation, we could track objects across frames
                frame_masks = []
                frame_object_ids = []
                
                for i, mask_data in enumerate(masks):
                    print(f"DEBUG: Processing mask {i}, type: {type(mask_data)}")
                    print(f"DEBUG: Mask keys: {mask_data.keys() if hasattr(mask_data, 'keys') else 'No keys method'}")
                    
                    # Store full mask data with all metadata
                    full_mask_data = {
                        'segmentation': mask_data['segmentation'].tolist(),
                        'area': int(mask_data['area']),
                        'bbox': mask_data['bbox'].tolist() if hasattr(mask_data['bbox'], 'tolist') else mask_data['bbox'],
                        'predicted_iou': float(mask_data['predicted_iou']),
                        'point_coords': mask_data['point_coords'].tolist() if hasattr(mask_data['point_coords'], 'tolist') else mask_data['point_coords'],
                        'stability_score': float(mask_data['stability_score']),
                        'crop_box': mask_data['crop_box'].tolist() if hasattr(mask_data['crop_box'], 'tolist') else mask_data['crop_box']
                    }
                    
                    frame_masks.append(full_mask_data)
                    frame_object_ids.append(i + 1)
                
                frame_results = {
                    'frame_idx': frame_idx,
                    'object_ids': frame_object_ids,
                    'masks': frame_masks,
                    'timestamp': time.time()
                }
                segmentation_results.append(frame_results)
                
                # Initialize object tracking for first frame
                if frame_idx == 0:
                    for i, mask_data in enumerate(masks):
                        object_tracking[i + 1] = {
                            'first_frame': frame_idx,
                            'initial_mask': mask_data['segmentation'].tolist()
                        }
            
            return {
                'video_path': video_path,
                'total_frames': frame_count_total,
                'segmentation_results': segmentation_results,
                'object_tracking': object_tracking,
                'processing_time': time.time(),
                'note': 'Real SAM2 automatic mask generator processing completed'
            }
            
        except Exception as e:
            print(f"SAM2 automatic mask generator failed: {e}")
            return self._simulate_processing(video_path, frame_count_total, width, height)

    def _process_with_video_predictor(self, video_path: str, prompts: List[Dict[str, Any]], frame_count_total: int, width: int, height: int) -> Dict[str, Any]:
        """Process video using SAM2 video predictor."""
        print("Using SAM2 video predictor...")
        
        # Convert MP4 path to JPEG folder path
        jpeg_folder_path = video_path.replace('.mp4', '')
        
        if not os.path.exists(jpeg_folder_path):
            print("JPEG folder not found, falling back to simulated processing...")
            return self._simulate_processing(video_path, frame_count_total, width, height)
        
        try:
            # Initialize SAM2 state with JPEG folder
            device = "cpu" if not torch.cuda.is_available() else "cuda"
            state = self.predictor.init_state(jpeg_folder_path)
            
            # Process prompts if provided
            segmentation_results = []
            object_tracking = {}
            
            if prompts and len(prompts) > 0:
                first_prompt = prompts[0]
                if 'prompts' in first_prompt:
                    prompt_points = []
                    prompt_labels = []
                    
                    for prompt in first_prompt['prompts']:
                        if prompt['type'] == 'point':
                            prompt_points.append(prompt['coordinates'])
                            prompt_labels.append(prompt['label'])
                    
                    if prompt_points:
                        points = np.array(prompt_points)
                        labels = np.array(prompt_labels)
                        
                        frame_idx_result, object_ids, masks = self.predictor.add_new_points_or_box(
                            state, points, labels
                        )
                        
                        frame_results = {
                            'frame_idx': frame_idx_result,
                            'object_ids': object_ids.tolist() if hasattr(object_ids, 'tolist') else object_ids,
                            'masks': [mask.tolist() for mask in masks] if hasattr(masks[0], 'tolist') else masks,
                            'timestamp': time.time()
                        }
                        segmentation_results.append(frame_results)
                        
                        for i, obj_id in enumerate(object_ids):
                            object_tracking[obj_id] = {
                                'first_frame': frame_idx_result,
                                'initial_mask': masks[i].tolist() if hasattr(masks[i], 'tolist') else masks[i]
                            }
            
            return {
                'video_path': video_path,
                'total_frames': frame_count_total,
                'segmentation_results': segmentation_results,
                'object_tracking': object_tracking,
                'processing_time': time.time(),
                'note': 'Real SAM2 video predictor processing completed'
            }
            
        except Exception as e:
            print(f"SAM2 video predictor failed: {e}")
            return self._simulate_processing(video_path, frame_count_total, width, height)

# Global model instance
ai_model: Optional[Sam2HieraTinyModel] = None
try:
    ai_model = Sam2HieraTinyModel()
    print(f"SAM2 model initialization completed. Model available: {ai_model.model_available}")
except Exception as e:
    print(f"ERROR: Failed to load AI model at startup: {e}")

# SAM2 video processing task function
def _sam2_video_processing_task(task_id: str, progress_callback: callable, relative_video_path: str, prompts: List[Dict[str, Any]] = None, mode: str = "automatic_mask_generator"):
    """SAM2 video processing task function."""
    global ai_model
    
    print(f"Task {task_id}: SAM2 processing started for video: {relative_video_path}")
    
    if ai_model is None:
        raise Exception("AI model failed to load at startup or is not available.")
    
    progress_callback(0.1)
    print(f"Task {task_id}: AI model is available")
    
    full_video_path = os.path.join(VIDEO_BASE_DIR, relative_video_path)
    print(f"Task {task_id}: Full video path: {full_video_path}")
    
    if not os.path.exists(full_video_path):
        raise Exception(f"Video file not found: {full_video_path}")
    
    print(f"Task {task_id}: Video file exists, proceeding with processing")
    
    # Use default prompts if none provided
    if prompts is None:
        prompts = [{
            'frame_idx': 0,
            'prompts': [{'type': 'point', 'coordinates': [320, 240], 'label': 1}]
        }]
    
    print(f"Task {task_id}: Using prompts: {prompts}")
    
    progress_callback(0.2)
    
    # Call the SAM2 processing
    try:
        result = ai_model.process_video(full_video_path, prompts, mode)
    except Exception as e:
        print(f"Task {task_id}: SAM2 processing failed: {e}")
        if "Only MP4 video and JPEG folder are supported" in str(e):
            print(f"Task {task_id}: SAM2 rejected video format, using simulated processing...")
            original_model_available = ai_model.model_available
            ai_model.model_available = False
            try:
                result = ai_model.process_video(full_video_path, prompts, mode)
            finally:
                ai_model.model_available = original_model_available
        else:
            raise e
    
    print(f"Task {task_id}: SAM2 processing completed")
    
    # Automatically generate visualization if processing was successful
    try:
        print(f"Task {task_id}: Generating visualization...")
        viz_result = create_simple_visualization(task_id, result)
        result['visualization'] = viz_result
        print(f"Task {task_id}: Visualization generated successfully")
    except Exception as viz_error:
        print(f"Task {task_id}: Visualization generation failed: {viz_error}")
        result['visualization_error'] = str(viz_error)
    
    return result