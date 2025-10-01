import React, { useState, useEffect } from 'react';

interface VideoPlayerProps {
  episodePath: string;
  episodeName: string;
  scenarioName: string;
  sceneName: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ 
  episodePath, 
  episodeName, 
  scenarioName, 
  sceneName 
}) => {
  const [runAI, setRunAI] = useState(false);
  const [aiTaskId, setAiTaskId] = useState<string | null>(null);
  const [aiTaskStatus, setAiTaskStatus] = useState<any>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  // Construct the full video URL
  const videoUrl = `http://localhost:8000${episodePath}`;
  
  // Construct the relative video path for SAM2 API
  const getVideoRelativePath = () => {
    return episodePath.replace('/video/', '');
  };

  const startAIProcessing = async () => {
    try {
      setAiError(null);
      
      const response = await fetch('http://localhost:8000/api/v1/ai/process-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_relative_path: getVideoRelativePath(),
          prompts: [{
            frame_idx: 0,
            prompts: [{
              type: 'point',
              coordinates: [160, 120],
              label: 1
            }]
          }],
          mode: 'automatic_mask_generator'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.data?.task_id) {
        setAiTaskId(data.data.task_id);
        setAiTaskStatus({ status: 'PENDING', progress: 0 });
      } else {
        throw new Error(data.message || 'Failed to start AI processing');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setAiError(errorMessage);
    }
  };

  const checkAITaskStatus = async () => {
    if (!aiTaskId) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/ai/tasks/${aiTaskId}`);
      
      if (!response.ok) {
        console.error(`HTTP error! status: ${response.status}`);
        return;
      }
      
      const data = await response.json();
      
      if (data.success && data.data) {
        setAiTaskStatus(data.data);
      }
    } catch (error) {
      console.error('Failed to check AI task status:', error);
    }
  };

  // Start AI processing when runAI is toggled on
  useEffect(() => {
    if (runAI && !aiTaskId && !aiError) {
      startAIProcessing();
    } else if (!runAI && aiTaskId) {
      // Reset AI state when toggled off
      setAiTaskId(null);
      setAiTaskStatus(null);
      setAiError(null);
    }
  }, [runAI, aiTaskId, aiError, startAIProcessing]);

  // Poll for AI task status when task is running
  useEffect(() => {
    if (aiTaskId && aiTaskStatus?.status !== 'COMPLETED' && aiTaskStatus?.status !== 'FAILED') {
      const interval = setInterval(checkAITaskStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [aiTaskId, aiTaskStatus?.status, checkAITaskStatus]);

  // Get visualization video URL if available
  const getVisualizationUrl = () => {
    if (aiTaskStatus?.status === 'COMPLETED' && aiTaskStatus?.result?.visualization) {
      return `http://localhost:8000${aiTaskStatus.result.visualization.visualization_path}`;
    }
    return null;
  };

  const visualizationUrl = getVisualizationUrl();

  return (
    <div className="video-player-container">
      <div className="video-header">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">{episodeName}</h2>
          <p className="text-sm text-gray-600">
            {scenarioName} / {sceneName}
          </p>
        </div>
        
        <div className="ai-controls">
          <label className="ai-toggle">
            <input
              type="checkbox"
              checked={runAI}
              onChange={(e) => setRunAI(e.target.checked)}
              disabled={aiTaskStatus?.status === 'RUNNING'}
            />
            <span className="toggle-slider"></span>
            <span className="toggle-label">Run AI</span>
          </label>
          
          {aiTaskId && (
            <div className="ai-status">
              <div className={`status-indicator ${aiTaskStatus?.status === 'COMPLETED' ? 'success' : aiTaskStatus?.status === 'FAILED' ? 'error' : 'pending'}`}></div>
              <span className="text-sm text-gray-700">
                {aiTaskStatus?.status === 'RUNNING' && `Processing... ${Math.round((aiTaskStatus.progress || 0) * 100)}%`}
                {aiTaskStatus?.status === 'COMPLETED' && 'AI Processing Complete'}
                {aiTaskStatus?.status === 'FAILED' && 'AI Processing Failed'}
                {aiTaskStatus?.status === 'PENDING' && 'AI Processing Pending'}
              </span>
              {aiTaskStatus?.status === 'RUNNING' && (
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ width: `${(aiTaskStatus.progress || 0) * 100}%` }}
                  ></div>
                </div>
              )}
            </div>
          )}
          
          {aiError && (
            <div className="text-red-600 text-sm mt-1">
              Error: {aiError}
            </div>
          )}
        </div>
      </div>

      <div className="video-content">
        <div className="video-grid">
          {/* Original Video Section */}
          <div className="video-section">
            <div className="video-label">Original Video</div>
            <div className="video-wrapper">
              <video 
                src={videoUrl}
                controls
                className="video-display"
              />
            </div>
          </div>

          {/* SAM2 Visualization Section */}
          <div className="video-section">
            <div className="video-label">SAM2 Segmentation</div>
            <div className="video-wrapper">
              {visualizationUrl ? (
                <video 
                  src={visualizationUrl}
                  controls
                  autoPlay
                  className="video-display"
                />
              ) : runAI || aiTaskStatus?.status === 'RUNNING' || aiTaskStatus?.status === 'PENDING' ? (
                <div className="video-placeholder">
                  <div className="placeholder-content">
                    <div className="spinner"></div>
                    <p>Generating SAM2 visualization...</p>
                    {(aiTaskStatus?.status === 'RUNNING' || runAI) && (
                      <p className="text-sm text-gray-500">
                        Progress: {Math.round((aiTaskStatus?.progress || 0) * 100)}%
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="video-placeholder">
                  <div className="placeholder-content">
                    <p>Enable AI processing to generate segmentation visualization</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;