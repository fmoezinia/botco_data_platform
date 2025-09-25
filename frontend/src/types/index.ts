export interface Episode {
  id: string;
  scene_id: string;
  name: string;
  filename: string;
  file_path: string;
  duration: number;
  frame_count: number;
  fps: number;
  width: number;
  height: number;
  created_at: string;
  description?: string;
}

export interface Scene {
  id: string;
  scenario_id: string;
  name: string;
  description: string;
  episode_count: number;
  total_duration: number;
  created_at: string;
  episodes: Episode[];
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  scene_count: number;
  total_episodes: number;
  total_duration: number;
  created_at: string;
  scenes: Scene[];
}

export interface VideoMetadata {
  id: string;
  filename: string;
  duration: number;
  frame_count: number;
  fps: number;
  width: number;
  height: number;
  file_path: string;
  created_at: string;
}

export interface Annotation {
  id: string;
  video_id: string;
  frame_number: number;
  annotation_type: string;
  coordinates: any;
  label: string;
  confidence: number;
  created_at: string;
}
