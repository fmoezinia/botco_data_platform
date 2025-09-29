"""
SAM2 Video Visualization Module
Creates visualization videos from SAM2 segmentation results.
"""
import os
import cv2
import numpy as np
import colorsys
from typing import Dict, Any, List


def generate_colors(num_colors: int) -> List[List[int]]:
    """Generate distinct colors for segmentation masks"""
    colors = []
    for i in range(num_colors):
        hue = i / num_colors
        saturation = 0.8
        value = 0.9
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append([int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255)])  # BGR format
    return colors


def create_visualization_video(
    sam2_task_id: str, 
    segmentation_results: List[Dict[str, Any]], 
    video_path: str
) -> Dict[str, Any]:
    """
    Create a visualization video from SAM2 results using JPEG frames
    
    Args:
        sam2_task_id: ID of the SAM2 task
        segmentation_results: List of segmentation results from SAM2
        video_path: Path to the original video file
        
    Returns:
        Dictionary containing visualization metadata
    """
    if not segmentation_results:
        raise Exception("No segmentation results found")
    
    # Get the JPEG folder path (same as video path but without .mp4)
    jpeg_folder_path = video_path.replace('.mp4', '')
    if not os.path.exists(jpeg_folder_path):
        raise Exception(f"JPEG folder not found: {jpeg_folder_path}")
    
    # Get list of JPEG files
    jpeg_files = [f for f in os.listdir(jpeg_folder_path) if f.endswith('.jpg')]
    jpeg_files.sort()
    
    if not jpeg_files:
        raise Exception(f"No JPEG files found in folder: {jpeg_folder_path}")
    
    # Load first frame to get dimensions
    first_frame_path = os.path.join(jpeg_folder_path, jpeg_files[0])
    first_frame = cv2.imread(first_frame_path)
    height, width = first_frame.shape[:2]
    
    # Create output directory
    output_dir = "data/visualizations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create output video (use 30 FPS as default)
    fps = 30.0
    output_path = f"{output_dir}/sam2_visualization_{sam2_task_id}.mp4"
    # Use H.264 codec (avc1) for better browser compatibility
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Generate colors for each object
    max_objects = 0
    for seg in segmentation_results:
        object_ids = seg.get('object_ids', [])
        if isinstance(object_ids, list):
            max_objects = max(max_objects, len(object_ids))
        else:
            print(f"Warning: object_ids is not a list: {type(object_ids)}")
    
    colors = generate_colors(max_objects + 1)  # +1 for safety
    
    processed_frames = 0
    
    # Process each JPEG frame
    for frame_idx, jpeg_file in enumerate(jpeg_files):
        frame_path = os.path.join(jpeg_folder_path, jpeg_file)
        frame = cv2.imread(frame_path)
        
        if frame is None:
            continue
        
        # Find segmentation results for this frame
        frame_segmentation = None
        for seg in segmentation_results:
            if seg.get('frame_idx') == frame_idx:
                frame_segmentation = seg
                break
        
        # Create overlay frame
        overlay = frame.copy()
        
        if frame_segmentation:
            object_ids = frame_segmentation.get('object_ids', [])
            masks = frame_segmentation.get('masks', [])
            
            # Ensure object_ids and masks are lists
            if not isinstance(object_ids, list):
                print(f"Warning: object_ids is not a list: {type(object_ids)}")
                object_ids = []
            if not isinstance(masks, list):
                print(f"Warning: masks is not a list: {type(masks)}")
                masks = []
            
            # Apply masks with colors
            for i, (obj_id, mask_data) in enumerate(zip(object_ids, masks)):
                if i < len(colors):
                    color = colors[i]
                    
                    # Extract segmentation mask
                    if isinstance(mask_data, dict):
                        mask_array = np.array(mask_data['segmentation'], dtype=np.uint8)
                        
                        # Get additional mask info
                        area = mask_data.get('area', 0)
                        bbox = mask_data.get('bbox', [0, 0, 0, 0])
                        predicted_iou = mask_data.get('predicted_iou', 0.0)
                        stability_score = mask_data.get('stability_score', 0.0)
                    else:
                        # Fallback for old format
                        mask_array = np.array(mask_data, dtype=np.uint8)
                        area = np.sum(mask_array > 0)
                        bbox = [0, 0, 0, 0]
                        predicted_iou = 0.0
                        stability_score = 0.0
                    
                    # Create colored overlay
                    colored_mask = np.zeros_like(overlay)
                    colored_mask[mask_array > 0] = color
                    
                    # Blend with original frame (30% opacity for colored masks)
                    overlay = cv2.addWeighted(overlay, 0.7, colored_mask, 0.3, 0)
                    
                    # Add object ID and info text
                    if np.any(mask_array > 0):
                        # Find center of mask
                        y_coords, x_coords = np.where(mask_array > 0)
                        if len(y_coords) > 0:
                            center_y, center_x = int(np.mean(y_coords)), int(np.mean(x_coords))
                            
                            # Add object ID
                            cv2.putText(overlay, f"ID:{obj_id}", (center_x, center_y), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                            
                            # Add quality scores (smaller text)
                            if isinstance(mask_data, dict):
                                score_text = f"IoU:{predicted_iou:.2f} S:{stability_score:.2f}"
                                cv2.putText(overlay, score_text, (center_x, center_y + 20), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Add frame info overlay
        cv2.putText(overlay, f"Frame: {frame_idx}/{len(jpeg_files)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        object_count = len(frame_segmentation.get('object_ids', [])) if frame_segmentation else 0
        cv2.putText(overlay, f"Objects: {object_count}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add SAM2 info
        cv2.putText(overlay, "SAM2 Segmentation", (10, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        out.write(overlay)
        processed_frames += 1
    
    out.release()
    
    return {
        "visualization_path": f"/static/visualizations/sam2_visualization_{sam2_task_id}.mp4",
        "local_path": output_path,
        "original_video": video_path,
        "jpeg_folder": jpeg_folder_path,
        "total_frames": len(jpeg_files),
        "processed_frames": processed_frames,
        "segmentation_results": len(segmentation_results),
        "sam2_task_id": sam2_task_id
    }


def create_simple_visualization(sam2_task_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple wrapper function to create visualization from SAM2 task result
    
    Args:
        sam2_task_id: ID of the SAM2 task
        result: Complete result from SAM2 processing
        
    Returns:
        Dictionary containing visualization metadata
    """
    segmentation_results = result.get('segmentation_results', [])
    video_path = result.get('video_path', '')
    
    return create_visualization_video(sam2_task_id, segmentation_results, video_path)
