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
  // Use the passed-in AI state instead of local state
  const runAI = aiState?.runAI || false;
  const aiTaskId = aiState?.aiTaskId || null;
  const aiTaskStatus = aiState?.aiTaskStatus || null;
  const aiError = aiState?.aiError || null;

  // Construct the full video URL
  const videoUrl = `http://localhost:8000${episodePath}`;
  
  // Construct the relative video path for SAM2 API
  const getVideoRelativePath = () => {
    // episodePath is like "/video/scenario/scene/episode.mp4"
    // We need "scenario/scene/episode.mp4" for the SAM2 API
    return episodePath.replace('/video/', '');
  };

  // Start AI processing when runAI is toggled on
  useEffect(() => {
    if (runAI && !aiTaskId) {
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
  }, [runAI, aiTaskId]);

  // Poll AI task status
  useEffect(() => {
    if (aiTaskId && aiTaskStatus?.status !== 'COMPLETED' && aiTaskStatus?.status !== 'FAILED') {
      const interval = setInterval(checkAITaskStatus, 2000); // Check every 2 seconds
      return () => clearInterval(interval);
    }
  }, [aiTaskId, aiTaskStatus?.status]);

  const startAIProcessing = async () => {
    try {
      onAiStateChange({ aiError: null });
      const response = await fetch('http://localhost:8000/ai/process-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_relative_path: getVideoRelativePath(),
          prompts: null // No specific prompts for now
        }),
      });

      if (!response.ok) {
        throw new Error(`AI service error: ${response.statusText}`);
      }

      const data = await response.json();
      onAiStateChange({ aiTaskId: data.task_id });
      console.log('AI processing started:', data.task_id);
    } catch (error) {
      console.error('Error starting AI processing:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      onAiStateChange({ 
        aiError: errorMessage,
        runAI: false 
      });
    }
  };

  const checkAITaskStatus = async () => {
    if (!aiTaskId) return;

    try {
      console.log('🔍 DEBUG: Checking AI task status for:', aiTaskId);
      const response = await fetch(`http://localhost:8000/ai/task-status/${aiTaskId}`);
      if (response.ok) {
        const status: AITaskStatus = await response.json();
        const previousStatus = aiTaskStatus?.status;
        
        console.log('🔍 DEBUG: AI task status response:', status);
        console.log('🔍 DEBUG: Previous status:', previousStatus);
        console.log('🔍 DEBUG: Current status:', status.status);
        
        onAiStateChange({ aiTaskStatus: status });
        
        // Only log when status changes to finished
        if ((status.status === 'COMPLETED' || status.status === 'FAILED') && 
            previousStatus !== 'COMPLETED' && previousStatus !== 'FAILED') {
          console.log('🎉 AI task finished:', status);
          console.log('🎉 Result:', status.result);
          console.log('🎉 Visualization:', status.result?.visualization);
        }
      }
    } catch (error) {
      console.error('Error checking AI task status:', error);
    }
  };

  // Get visualization video URL if available
  const getVisualizationUrl = () => {
    console.log('🔍 DEBUG: getVisualizationUrl called');
    console.log('🔍 DEBUG: aiTaskStatus:', aiTaskStatus);
    console.log('🔍 DEBUG: aiTaskStatus?.status:', aiTaskStatus?.status);
    console.log('🔍 DEBUG: aiTaskStatus?.result:', aiTaskStatus?.result);
    console.log('🔍 DEBUG: aiTaskStatus?.result?.visualization:', aiTaskStatus?.result?.visualization);
    
    if (aiTaskStatus?.status === 'COMPLETED' && aiTaskStatus?.result?.visualization) {
      const url = `http://localhost:8000${aiTaskStatus.result.visualization.visualization_path}`;
      console.log('🔍 DEBUG: Generated visualization URL:', url);
      return url;
    }
    console.log('🔍 DEBUG: No visualization URL available');
    return null;
  };

  const visualizationUrl = getVisualizationUrl();
  console.log('🔍 DEBUG: Final visualizationUrl:', visualizationUrl);

  return (
    <div className="video-player-container">
      <div className="video-header">
        <h2>{scenarioName} - {sceneName} - Episode {episodeName}</h2>
        
        {/* RunAI Toggle */}
        <div className="ai-controls">
          <label className="ai-toggle">
            <input
              type="checkbox"
              checked={runAI}
              onChange={(e) => onAiStateChange({ runAI: e.target.checked })}
            />
            <span className="toggle-label">RunAI</span>
          </label>
          
          {/* AI Status Display */}
          {aiTaskId && (
            <div className="ai-status">
              <div className="ai-task-info">
                <strong>AI Task:</strong> {aiTaskId.substring(0, 8)}...
              </div>
              {aiTaskStatus && (
                <div className="ai-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${aiTaskStatus.progress * 100}%` }}
                    />
                  </div>
                  <span className="progress-text">
                    {aiTaskStatus.status} ({Math.round(aiTaskStatus.progress * 100)}%)
                  </span>
                </div>
              )}
              {aiTaskStatus?.status === 'COMPLETED' && (
                <div className="ai-result">✅ AI processing completed!</div>
              )}
              {aiTaskStatus?.status === 'FAILED' && (
                <div className="ai-error">❌ AI processing failed: {aiTaskStatus.error}</div>
              )}
            </div>
          )}
          
          {aiError && (
            <div className="ai-error">❌ {aiError}</div>
          )}
          
          {/* Debug Information */}
          <div style={{ 
            background: 'rgba(0,0,0,0.8)', 
            padding: '10px', 
            marginTop: '10px', 
            borderRadius: '5px',
            fontSize: '12px',
            fontFamily: 'monospace'
          }}>
            <div><strong>DEBUG INFO:</strong></div>
            <div>AI Task ID: {aiTaskId || 'None'}</div>
            <div>AI Status: {aiTaskStatus?.status || 'None'}</div>
            <div>Visualization URL: {visualizationUrl || 'None'}</div>
            <div>Has Visualization: {aiTaskStatus?.result?.visualization ? 'Yes' : 'No'}</div>
            {aiTaskStatus?.result?.visualization && (
              <div>Visualization Path: {aiTaskStatus.result.visualization.visualization_path}</div>
            )}
          </div>
        </div>
      </div>
      
      <div className="video-content">
        <div className="video-grid">
          {/* Original Video */}
          <div className="video-section">
            <div className="video-label">Original Video</div>
            <div className="video-wrapper">
              <video 
                src={videoUrl}
                controls
                autoPlay
                className="video-display"
              />
            </div>
          </div>
          
          {/* SAM2 Visualization Video */}
          <div className="video-section">
            <div className="video-label">
              SAM2 Segmentation
              {visualizationUrl ? (
                <span className="status-indicator success">✓ Ready</span>
              ) : aiTaskStatus?.status === 'COMPLETED' ? (
                <span className="status-indicator error">✗ No visualization</span>
              ) : aiTaskStatus?.status === 'RUNNING' ? (
                <span className="status-indicator pending">⏳ Processing...</span>
              ) : (
                <span className="status-indicator empty">○ Empty</span>
              )}
            </div>
            <div className="video-wrapper">
              {visualizationUrl ? (
                <video 
                  src={visualizationUrl}
                  controls
                  autoPlay
                  className="video-display"
                  onLoadStart={() => console.log('🎬 DEBUG: Visualization video load started')}
                  onLoadedMetadata={() => console.log('🎬 DEBUG: Visualization video metadata loaded')}
                  onLoadedData={() => console.log('🎬 DEBUG: Visualization video data loaded')}
                  onCanPlay={() => console.log('🎬 DEBUG: Visualization video can play')}
                  onPlay={() => console.log('🎬 DEBUG: Visualization video started playing')}
                  onError={(e) => console.error('🎬 DEBUG: Visualization video error:', e)}
                  onLoad={() => console.log('🎬 DEBUG: Visualization video load complete')}
                />
              ) : (
                <div className="video-placeholder">
                  <div className="placeholder-content">
                    {aiTaskStatus?.status === 'RUNNING' ? (
                      <>
                        <div className="spinner"></div>
                        <p>Generating SAM2 visualization...</p>
                        <small>{Math.round(aiTaskStatus.progress * 100)}% complete</small>
                      </>
                    ) : (
                      <>
                        <div className="placeholder-icon">🎬</div>
                        <p>No visualization yet</p>
                        <small>Toggle "RunAI" to generate SAM2 segmentation</small>
                      </>
                    )}
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