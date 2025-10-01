import React, { useState, useEffect } from 'react';

interface EpisodeDataGraphProps {
  episodePath: string;
}

interface DataPoint {
  time: number;
  left_waist: {
    observation_state: number;
    action: number;
  };
  left_forearm_roll: {
    observation_state: number;
    action: number;
  };
  left_wrist_rotate: {
    observation_state: number;
    action: number;
  };
}

const EpisodeDataGraph: React.FC<EpisodeDataGraphProps> = ({ episodePath }) => {
  const [data, setData] = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEpisodeData();
  }, [episodePath]);

  const fetchEpisodeData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Extract episode path for API call
      const episodePathForApi = episodePath.replace('/video/', '');
      
      console.log('📊 Fetching episode data for:', episodePathForApi);
      
      const response = await fetch(`http://localhost:8000/api/v1/scenarios/episodes/${episodePathForApi}/data`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('📊 Episode data response:', result);
      
      if (result.success && result.data?.data_points) {
        setData(result.data.data_points);
        console.log('✅ Episode data loaded successfully');
      } else {
        throw new Error(result.message || 'Failed to load episode data');
      }
      
    } catch (err) {
      console.error('❌ Failed to fetch episode data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch episode data');
      
      // Fallback to mock data if API fails
      console.log('🔄 Falling back to mock data');
      const mockData: DataPoint[] = generateMockData();
      setData(mockData);
    } finally {
      setLoading(false);
    }
  };

  const generateMockData = (): DataPoint[] => {
    const data: DataPoint[] = [];
    const timePoints = 100; // 100 data points from 0 to 8 seconds
    
    for (let i = 0; i < timePoints; i++) {
      const time = (i / timePoints) * 8;
      
      // Generate data similar to the image
      const left_waist = {
        observation_state: -0.01 + Math.sin(time * 0.5) * 0.005,
        action: -0.01 + Math.sin(time * 0.5) * 0.005 + (Math.random() - 0.5) * 0.002
      };
      
      const left_forearm_roll = {
        observation_state: time < 1 ? 0 : time < 3 ? -0.135 * (time - 1) / 2 : time < 6 ? -0.135 : -0.135 + 0.065 * (time - 6) / 2,
        action: time < 1 ? 0 : time < 3 ? -0.135 * (time - 1) / 2 : time < 6 ? -0.135 : -0.135 + 0.065 * (time - 6) / 2
      };
      
      const left_wrist_rotate = {
        observation_state: time < 2 ? 0.045 * time / 2 : time < 6 ? 0.045 - 0.18 * (time - 2) / 4 : 0.045 - 0.18 + 0.155 * (time - 6) / 2,
        action: time < 2 ? 0.045 * time / 2 : time < 6 ? 0.045 - 0.18 * (time - 2) / 4 : 0.045 - 0.18 + 0.155 * (time - 6) / 2
      };
      
      data.push({
        time,
        left_waist,
        left_forearm_roll,
        left_wrist_rotate
      });
    }
    
    return data;
  };

  const renderGraph = () => {
    if (loading) {
      return (
        <div className="graph-loading">
          <div className="spinner"></div>
          <p>Loading episode data...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="graph-error">
          <p>Error loading episode data: {error}</p>
        </div>
      );
    }

    if (data.length === 0) {
      return (
        <div className="graph-empty">
          <p>No episode data available</p>
        </div>
      );
    }

    // Get the last data point for current values
    const lastPoint = data[data.length - 1];

    return (
      <div className="episode-graph">
        <svg className="graph-svg" viewBox="0 0 800 400">
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="40" height="20" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5" opacity="0.3"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Axes */}
          <line x1="60" y1="20" x2="60" y2="380" stroke="#6B7280" strokeWidth="2"/>
          <line x1="60" y1="380" x2="740" y2="380" stroke="#6B7280" strokeWidth="2"/>
          
          {/* Y-axis labels */}
          <text x="50" y="30" textAnchor="end" fill="#9CA3AF" fontSize="12">0.045</text>
          <text x="50" y="110" textAnchor="end" fill="#9CA3AF" fontSize="12">0</text>
          <text x="50" y="190" textAnchor="end" fill="#9CA3AF" fontSize="12">-0.045</text>
          <text x="50" y="270" textAnchor="end" fill="#9CA3AF" fontSize="12">-0.09</text>
          <text x="50" y="350" textAnchor="end" fill="#9CA3AF" fontSize="12">-0.135</text>
          
          {/* X-axis labels */}
          <text x="100" y="395" textAnchor="middle" fill="#9CA3AF" fontSize="12">0</text>
          <text x="200" y="395" textAnchor="middle" fill="#9CA3AF" fontSize="12">2</text>
          <text x="300" y="395" textAnchor="middle" fill="#9CA3AF" fontSize="12">4</text>
          <text x="400" y="395" textAnchor="middle" fill="#9CA3AF" fontSize="12">6</text>
          <text x="500" y="395" textAnchor="middle" fill="#9CA3AF" fontSize="12">8</text>
          
          {/* Data lines */}
          {data.map((point, index) => {
            if (index === 0) return null;
            const prevPoint = data[index - 1];
            
            const x1 = 60 + (prevPoint.time / 8) * 680;
            const y1 = 200 - (prevPoint.left_waist.observation_state / 0.18) * 180;
            const x2 = 60 + (point.time / 8) * 680;
            const y2 = 200 - (point.left_waist.observation_state / 0.18) * 180;
            
            const x1Action = 60 + (prevPoint.time / 8) * 680;
            const y1Action = 200 - (prevPoint.left_waist.action / 0.18) * 180;
            const x2Action = 60 + (point.time / 8) * 680;
            const y2Action = 200 - (point.left_waist.action / 0.18) * 180;
            
            return (
              <g key={index}>
                {/* left_waist observation state (solid red) */}
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#EF4444" strokeWidth="2"/>
                {/* left_waist action (dashed red) */}
                <line x1={x1Action} y1={y1Action} x2={x2Action} y2={y2Action} stroke="#EF4444" strokeWidth="2" strokeDasharray="5,5"/>
                
                {/* left_forearm_roll observation state (solid green) */}
                <line x1={x1} y1={200 - (prevPoint.left_forearm_roll.observation_state / 0.18) * 180} 
                      x2={x2} y2={200 - (point.left_forearm_roll.observation_state / 0.18) * 180} 
                      stroke="#10B981" strokeWidth="2"/>
                {/* left_forearm_roll action (dashed green) */}
                <line x1={x1Action} y1={200 - (prevPoint.left_forearm_roll.action / 0.18) * 180} 
                      x2={x2Action} y2={200 - (point.left_forearm_roll.action / 0.18) * 180} 
                      stroke="#10B981" strokeWidth="2" strokeDasharray="5,5"/>
                
                {/* left_wrist_rotate observation state (solid blue) */}
                <line x1={x1} y1={200 - (prevPoint.left_wrist_rotate.observation_state / 0.18) * 180} 
                      x2={x2} y2={200 - (point.left_wrist_rotate.observation_state / 0.18) * 180} 
                      stroke="#3B82F6" strokeWidth="2"/>
                {/* left_wrist_rotate action (dashed blue) */}
                <line x1={x1Action} y1={200 - (prevPoint.left_wrist_rotate.action / 0.18) * 180} 
                      x2={x2Action} y2={200 - (point.left_wrist_rotate.action / 0.18) * 180} 
                      stroke="#3B82F6" strokeWidth="2" strokeDasharray="5,5"/>
              </g>
            );
          })}
        </svg>
        
        {/* Legend */}
        <div className="graph-legend">
          <div className="legend-item">
            <div className="legend-color red"></div>
            <span>left_waist</span>
            <div className="legend-values">
              <span>observation.state: {lastPoint.left_waist.observation_state.toFixed(2)}</span>
              <span>action: {lastPoint.left_waist.action.toFixed(2)}</span>
            </div>
          </div>
          <div className="legend-item">
            <div className="legend-color green"></div>
            <span>left_forearm_roll</span>
            <div className="legend-values">
              <span>observation.state: {lastPoint.left_forearm_roll.observation_state.toFixed(2)}</span>
              <span>action: {lastPoint.left_forearm_roll.action.toFixed(2)}</span>
            </div>
          </div>
          <div className="legend-item">
            <div className="legend-color blue"></div>
            <span>left_wrist_rotate</span>
            <div className="legend-values">
              <span>observation.state: {lastPoint.left_wrist_rotate.observation_state.toFixed(2)}</span>
              <span>action: {lastPoint.left_wrist_rotate.action.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="episode-data-graph">
      {renderGraph()}
    </div>
  );
};

export default EpisodeDataGraph;
