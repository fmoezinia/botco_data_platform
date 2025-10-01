import React, { useState, useRef, useEffect } from 'react';

interface Annotation {
  id: string;
  x: number;
  y: number;
  text: string;
  timestamp: number;
}

interface InteractiveVideoPlayerProps {
  videoUrl: string;
}

const InteractiveVideoPlayer: React.FC<InteractiveVideoPlayerProps> = ({ videoUrl }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editingAnnotation, setEditingAnnotation] = useState<Annotation | null>(null);
  const [tempText, setTempText] = useState('');

  const handleVideoClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current || !videoRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Check if click is in the bottom 20% (video controls area) - ignore clicks there
    const bottomThreshold = rect.height * 0.8;
    if (y > bottomThreshold) {
      return; // Don't create annotation in controls area
    }

    const timestamp = videoRef.current.currentTime;

    // Create new annotation
    const newAnnotation: Annotation = {
      id: Date.now().toString(),
      x: (x / rect.width) * 100, // Convert to percentage
      y: (y / rect.height) * 100, // Convert to percentage
      text: '',
      timestamp
    };

    setAnnotations(prev => [...prev, newAnnotation]);
    setEditingAnnotation(newAnnotation);
    setTempText('');
    setIsEditing(true);
  };

  const handleAnnotationClick = (annotation: Annotation, event: React.MouseEvent) => {
    event.stopPropagation();
    setEditingAnnotation(annotation);
    setTempText(annotation.text);
    setIsEditing(true);
  };

  const handleDeleteAnnotation = (id: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setAnnotations(prev => prev.filter(ann => ann.id !== id));
    if (editingAnnotation?.id === id) {
      setIsEditing(false);
      setEditingAnnotation(null);
    }
  };

  const handleTextSubmit = () => {
    if (!editingAnnotation) return;

    setAnnotations(prev => 
      prev.map(ann => 
        ann.id === editingAnnotation.id 
          ? { ...ann, text: tempText }
          : ann
      )
    );
    setIsEditing(false);
    setEditingAnnotation(null);
    setTempText('');
  };

  const handleTextCancel = () => {
    setIsEditing(false);
    setEditingAnnotation(null);
    setTempText('');
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleTextSubmit();
    } else if (event.key === 'Escape') {
      handleTextCancel();
    }
  };

  return (
    <div className="interactive-video-section">
      <div className="video-label">
        Interactive Annotation Player
        <div className="annotation-controls">
          <span className="annotation-count">
            {annotations.length} annotation{annotations.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>
      
      <div 
        className="interactive-video-wrapper"
        ref={containerRef}
        onClick={handleVideoClick}
      >
        <video 
          ref={videoRef}
          src={videoUrl}
          controls
          className="interactive-video-display"
        />
        
        {/* Annotations overlay */}
        <div className="annotations-overlay">
          {annotations.map((annotation) => (
            <div
              key={annotation.id}
              className="annotation-marker"
              style={{
                left: `${annotation.x}%`,
                top: `${annotation.y}%`,
              }}
              onClick={(e) => handleAnnotationClick(annotation, e)}
            >
              <div className="annotation-x">×</div>
              {annotation.text && (
                <div className="annotation-bubble">
                  {annotation.text}
                </div>
              )}
              <button 
                className="annotation-delete"
                onClick={(e) => handleDeleteAnnotation(annotation.id, e)}
                title="Delete annotation"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Text input modal */}
      {isEditing && editingAnnotation && (
        <div className="annotation-modal">
          <div className="annotation-modal-content">
            <h3>Add Annotation</h3>
            <p>Timestamp: {editingAnnotation.timestamp.toFixed(2)}s</p>
            <textarea
              value={tempText}
              onChange={(e) => setTempText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Enter your annotation text..."
              autoFocus
              rows={3}
            />
            <div className="annotation-modal-buttons">
              <button onClick={handleTextSubmit} className="btn-primary">
                Save
              </button>
              <button onClick={handleTextCancel} className="btn-secondary">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Annotations list */}
      {annotations.length > 0 && (
        <div className="annotations-list">
          <h4>Annotations ({annotations.length})</h4>
          <div className="annotations-items">
            {annotations
              .sort((a, b) => a.timestamp - b.timestamp)
              .map((annotation) => (
                <div key={annotation.id} className="annotation-item">
                  <div className="annotation-item-header">
                    <span className="annotation-timestamp">
                      {annotation.timestamp.toFixed(2)}s
                    </span>
                    <button 
                      onClick={(e) => handleDeleteAnnotation(annotation.id, e)}
                      className="annotation-item-delete"
                    >
                      ×
                    </button>
                  </div>
                  {annotation.text && (
                    <div className="annotation-item-text">
                      {annotation.text}
                    </div>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveVideoPlayer;
