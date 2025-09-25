import React, { useState, useEffect } from 'react';

interface VideoPlayerProps {
  episodePath: string;
  episodeName: string;
  scenarioName: string;
  sceneName: string;
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
  sceneName 
}) => {
  const [runAI, setRunAI] = useState(false);
  const [aiTaskId, setAiTaskId] = useState<string | null>(null);
  const [aiTaskStatus, setAiTaskStatus] = useState<AITaskStatus | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

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
      setAiTaskId(null);
      setAiTaskStatus(null);
      setAiError(null);
    }
  }, [runAI, aiTaskId]);

  // Poll AI task status
  useEffect(() => {
    if (aiTaskId) {
      const interval = setInterval(checkAITaskStatus, 2000); // Check every 2 seconds
      return () => clearInterval(interval);
    }
  }, [aiTaskId]);

  const startAIProcessing = async () => {
    try {
      setAiError(null);
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
      setAiTaskId(data.task_id);
      console.log('AI processing started:', data.task_id);
    } catch (error) {
      console.error('Error starting AI processing:', error);
      setAiError(error instanceof Error ? error.message : 'Unknown error');
      setRunAI(false);
    }
  };

  const checkAITaskStatus = async () => {
    if (!aiTaskId) return;

    try {
      const response = await fetch(`http://localhost:8000/ai/task-status/${aiTaskId}`);
      if (response.ok) {
        const status: AITaskStatus = await response.json();
        setAiTaskStatus(status);
        
        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          console.log('AI task finished:', status);
        }
      }
    } catch (error) {
      console.error('Error checking AI task status:', error);
    }
  };

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
              onChange={(e) => setRunAI(e.target.checked)}
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
        </div>
      </div>
      
      <div className="video-content">
        <div className="video-wrapper">
          <video 
            src={videoUrl}
            controls
            autoPlay
            className="video-display"
          />
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;