import React, { useState, useEffect } from 'react';

interface VideoPlayerProps {
  episodePath: string;
  episodeName: string;
  scenarioName: string;
  sceneName: string;
  aiState: {
    runAI: boolean;
    aiTaskId: string | null;
    aiTaskStatus: any | null;
    aiError: string | null;
  } | null;
  onAiStateChange: (updates: any) => void;
}

interface AITaskStatus {
  task_id: string;
  status: string;
  progress: number;
  result?: any;
  error?: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ 
  episodePath, 
  episodeName, 
  scenarioName, 
  sceneName,
  aiState,
  onAiStateChange
}) => {
  const runAI = aiState?.runAI || false;
  const aiTaskId = aiState?.aiTaskId || null;
  const aiTaskStatus = aiState?.aiTaskStatus || null;
  const aiError = aiState?.aiError || null;

  // Construct the full video URL
  const videoUrl = `http://localhost:8000${episodePath}`;
  
  // Construct the relative video path for SAM2 API
  const getVideoRelativePath = () => {
    return episodePath.replace('/video/', '');
  };

  // Start AI processing when runAI is toggled on
  useEffect(() => {
    if (runAI && !aiTaskId && !aiError) {
      startAIProcessing();
    } else if (!runAI && aiTaskId) {
      // Reset AI state when toggled off
      onAiStateChange({
        runAI: false,
        aiTaskId: null,
        aiTaskStatus: null,
        aiError: null
      });
    }
  }, [runAI, aiTaskId, aiError]);

  // Poll for AI task status when task is running
  useEffect(() => {
    if (aiTaskId && (aiTaskStatus?.status === 'RUNNING' || aiTaskStatus?.status === 'PENDING')) {
      console.log('🔄 Starting task polling for status:', aiTaskStatus?.status);
      const interval = setInterval(checkAITaskStatus, 2000);
      return () => {
        console.log('🛑 Stopping task polling');
        clearInterval(interval);
      };
    }
  }, [aiTaskId, aiTaskStatus?.status]);

  const startAIProcessing = async () => {
    try {
      onAiStateChange({ aiError: null });
      
      const videoPath = getVideoRelativePath();
      console.log('🎥 Video path being sent:', videoPath);
      console.log('🎥 Episode path:', episodePath);
      
      const requestBody = {
        video_relative_path: videoPath,
        prompts: [{
          frame_idx: 0,
          prompts: [{
            type: 'point',
            coordinates: [160, 120],
            label: 1
          }]
        }],
        mode: 'automatic_mask_generator'
      };
      console.log('📤 Request body:', requestBody);
      
      const response = await fetch('http://localhost:8000/api/v1/ai/process-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('🚀 AI processing response:', data);
      
      if (data.success && data.data?.task_id) {
        console.log('🎯 Setting AI task ID:', data.data.task_id);
        const stateUpdate = { 
          aiTaskId: data.data.task_id,
          aiTaskStatus: { status: 'PENDING', progress: 0 }
        };
        console.log('🔄 Calling onAiStateChange with:', stateUpdate);
        onAiStateChange(stateUpdate);
      } else {
        throw new Error(data.message || 'Failed to start AI processing');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      onAiStateChange({ aiError: errorMessage });
    }
  };

  const checkAITaskStatus = async () => {
    if (!aiTaskId) {
      console.log('❌ No AI task ID available for status check');
      return;
    }

    try {
      console.log(`🔍 Checking task status for ID: ${aiTaskId}`);
      const response = await fetch(`http://localhost:8000/api/v1/ai/tasks/${aiTaskId}`);
      const data = await response.json();
      
      console.log('📡 Task status response:', data);
      
      if (data.success && data.data) {
        console.log('✅ Updating task status:', data.data);
        const statusUpdate = { aiTaskStatus: data.data };
        console.log('🔄 Calling onAiStateChange with status update:', statusUpdate);
        onAiStateChange(statusUpdate);
        
        if (data.data.status === 'COMPLETED' || data.data.status === 'FAILED') {
          console.log(`🏁 Task finished with status: ${data.data.status}`);
          // Task finished, stop polling
          return;
        }
      } else {
        console.log('❌ Task status response not successful:', data);
      }
    } catch (error) {
      console.error('💥 Failed to check AI task status:', error);
    }
  };

  // Get visualization video URL if available
  const getVisualizationUrl = () => {
    console.log('🎬 Getting visualization URL...');
    console.log('📊 AI Task Status:', aiTaskStatus);
    console.log('📊 AI Task Result:', aiTaskStatus?.result);
    console.log('📊 Visualization:', aiTaskStatus?.result?.visualization);
    
    if (aiTaskStatus?.status === 'COMPLETED' && aiTaskStatus?.result?.visualization) {
      const url = `http://localhost:8000${aiTaskStatus.result.visualization.visualization_path}`;
      console.log('✅ Generated visualization URL:', url);
      return url;
    }
    console.log('❌ No visualization URL available');
    return null;
  };

  const visualizationUrl = getVisualizationUrl();

  // Debug current state
  console.log('🔍 Current AI State:', {
    aiTaskId,
    aiTaskStatus,
    runAI,
    visualizationUrl
  });

  const getStatusIndicator = () => {
    if (aiTaskStatus?.status === 'COMPLETED' && visualizationUrl) {
      return 'success';
    } else if (aiTaskStatus?.status === 'FAILED' || aiError) {
      return 'error';
    } else if (aiTaskStatus?.status === 'RUNNING' || aiTaskStatus?.status === 'PENDING') {
      return 'pending';
    }
    return 'empty';
  };

  const statusIndicator = getStatusIndicator();

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
              onChange={(e) => onAiStateChange({ runAI: e.target.checked })}
              disabled={aiTaskStatus?.status === 'RUNNING'}
            />
            <span className="toggle-slider"></span>
            <span className="toggle-label">Initiate background AI processing</span>
          </label>
          
          {aiTaskId && (
            <div className="ai-status">
              <div className={`status-indicator ${statusIndicator}`}></div>
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
            <div className="video-label">
              SAM2 Segmentation
              <div className={`status-indicator ${statusIndicator}`}></div>
            </div>
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
                    {aiTaskStatus?.result?.visualization_error && (
                      <p className="text-sm text-red-500">
                        Visualization Error: {aiTaskStatus.result.visualization_error}
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