import React, { useState, useEffect } from 'react';
import './App.css';
import VideoPlayer from './components/VideoPlayer';

function App() {
  const [expandedScenario, setExpandedScenario] = useState<string | null>(null);
  const [expandedScene, setExpandedScene] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [scenes, setScenes] = useState<{[key: string]: string[]}>({});
  const [episodes, setEpisodes] = useState<{[key: string]: string[]}>({});
  const [loading, setLoading] = useState(true);
  const [loadingScenes, setLoadingScenes] = useState<string | null>(null);
  const [loadingEpisodes, setLoadingEpisodes] = useState<string | null>(null);
  
  // Video player state
  const [selectedEpisode, setSelectedEpisode] = useState<{
    scenarioId: string;
    sceneId: string;
    episodeId: string;
    episodePath: string;
  } | null>(null);

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      console.log('Fetching scenarios...');
      const response = await fetch('http://localhost:8000/scenarios-list');
      const data = await response.json();
      console.log('Scenarios data:', data);
      setScenarios(data.scenarios || []);
    } catch (error) {
      console.error('Error fetching scenarios:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchScenes = async (scenarioId: string) => {
    setLoadingScenes(scenarioId);
    try {
      const response = await fetch(`http://localhost:8000/scenarios/${encodeURIComponent(scenarioId)}/scenes`);
      const data = await response.json();
      console.log('Scenes data:', data);
      setScenes(prev => ({ ...prev, [scenarioId]: data.scenes || [] }));
    } catch (error) {
      console.error('Error fetching scenes:', error);
    } finally {
      setLoadingScenes(null);
    }
  };

  const fetchEpisodes = async (scenarioId: string, sceneId: string) => {
    setLoadingEpisodes(`${scenarioId}-${sceneId}`);
    try {
      const response = await fetch(`http://localhost:8000/scenarios/${encodeURIComponent(scenarioId)}/scenes/${encodeURIComponent(sceneId)}/episodes`);
      const data = await response.json();
      console.log('Episodes data:', data);
      setEpisodes(prev => ({ ...prev, [`${scenarioId}-${sceneId}`]: data.episodes || [] }));
    } catch (error) {
      console.error('Error fetching episodes:', error);
    } finally {
      setLoadingEpisodes(null);
    }
  };

  const handleScenarioClick = (scenarioId: string) => {
    if (expandedScenario === scenarioId) {
      setExpandedScenario(null);
      setExpandedScene(null);
    } else {
      setExpandedScenario(scenarioId);
      setExpandedScene(null);
      if (!scenes[scenarioId]) {
        fetchScenes(scenarioId);
      }
    }
  };

  const handleSceneClick = (scenarioId: string, sceneId: string) => {
    if (expandedScene === sceneId) {
      setExpandedScene(null);
    } else {
      setExpandedScene(sceneId);
      if (!episodes[`${scenarioId}-${sceneId}`]) {
        fetchEpisodes(scenarioId, sceneId);
      }
    }
  };

  const handleEpisodeClick = (scenarioId: string, sceneId: string, episodeId: string) => {
    const episodePath = `/video/${scenarioId}/${sceneId}/${episodeId}`;
    setSelectedEpisode({
      scenarioId,
      sceneId,
      episodeId,
      episodePath
    });
  };

  const getEpisodeName = (episodeId: string) => {
    return episodeId.replace('.mp4', '');
  };

  const getSceneName = (sceneId: string) => {
    return sceneId.replace('scene_', 'Scene ').replace(/_/g, ' ');
  };

  const getScenarioName = (scenarioId: string) => {
    return scenarioId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading scenarios...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="main-container">
        {/* Sidebar */}
        <div className="sidebar">
          <div className="sidebar-header">
            <h1>Botco Data Platform</h1>
            <p>Video Analysis & AI Processing</p>
          </div>
          
          <div className="sidebar-content">
            <h2>Scenarios</h2>
            <div className="scenario-list">
              {scenarios.map(scenarioId => (
                <div key={scenarioId} className="scenario-item">
                  <div 
                    className="scenario-header"
                    onClick={() => handleScenarioClick(scenarioId)}
                  >
                    <span className="scenario-name">{getScenarioName(scenarioId)}</span>
                    <span className={`expand-icon ${expandedScenario === scenarioId ? 'expanded' : ''}`}>
                      ▼
                    </span>
                  </div>
                  
                  {expandedScenario === scenarioId && (
                    <div className="scenes-container">
                      {loadingScenes === scenarioId ? (
                        <div className="loading-scenes">
                          <div className="spinner small"></div>
                          <span>Loading scenes...</span>
                        </div>
                      ) : (
                        scenes[scenarioId]?.map(sceneId => (
                          <div key={sceneId} className="scene-item">
                            <div 
                              className="scene-header"
                              onClick={() => handleSceneClick(scenarioId, sceneId)}
                            >
                              <span className="scene-name">{getSceneName(sceneId)}</span>
                              <span className={`expand-icon ${expandedScene === sceneId ? 'expanded' : ''}`}>
                                ▼
                              </span>
                            </div>
                            
                            {expandedScene === sceneId && (
                              <div className="episodes-container">
                                {loadingEpisodes === `${scenarioId}-${sceneId}` ? (
                                  <div className="loading-episodes">
                                    <div className="spinner small"></div>
                                    <span>Loading episodes...</span>
                                  </div>
                                ) : (
                                  episodes[`${scenarioId}-${sceneId}`]?.map(episodeId => (
                                    <div 
                                      key={episodeId}
                                      className={`episode-item ${selectedEpisode?.episodeId === episodeId ? 'selected' : ''}`}
                                      onClick={() => handleEpisodeClick(scenarioId, sceneId, episodeId)}
                                    >
                                      {getEpisodeName(episodeId)}
                                    </div>
                                  ))
                                )}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="main-content">
          {selectedEpisode ? (
            <VideoPlayer
              episodePath={selectedEpisode.episodePath}
              episodeName={getEpisodeName(selectedEpisode.episodeId)}
              scenarioName={getScenarioName(selectedEpisode.scenarioId)}
              sceneName={getSceneName(selectedEpisode.sceneId)}
            />
          ) : (
            <div className="no-episode-selected">
              <h2>Welcome to Botco Data Platform</h2>
              <p>Select an episode from the sidebar to start viewing and analyzing videos.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;