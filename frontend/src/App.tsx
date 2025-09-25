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
      setScenes(prev => ({
        ...prev,
        [scenarioId]: data.scenes || []
      }));
    } catch (error) {
      console.error('Error fetching scenes:', error);
    } finally {
      setLoadingScenes(null);
    }
  };

  const fetchEpisodes = async (scenarioId: string, sceneId: string) => {
    const key = `${scenarioId}-${sceneId}`;
    setLoadingEpisodes(key);
    try {
      const response = await fetch(`http://localhost:8000/scenarios/${encodeURIComponent(scenarioId)}/scenes/${encodeURIComponent(sceneId)}/episodes`);
      const data = await response.json();
      console.log('episode data:', data);
      setEpisodes(prev => ({
        ...prev,
        [key]: data.episodes || []
      }));
    } catch (error) {
      console.error('Error fetching episodes:', error);
    } finally {
      setLoadingEpisodes(null);
    }
  };

  const toggleScenario = (scenarioId: string) => {
    if (expandedScenario === scenarioId) {
      setExpandedScenario(null);
      setExpandedScene(null);
    } else {
      setExpandedScenario(scenarioId);
      setExpandedScene(null);
      // Fetch scenes when opening a scenario
      if (!scenes[scenarioId]) {
        fetchScenes(scenarioId);
      }
    }
  };

  const toggleScene = (scenarioId: string, sceneId: string) => {
    const key = `${scenarioId}-${sceneId}`;
    if (expandedScene === key) {
      setExpandedScene(null);
    } else {
      setExpandedScene(key);
      // Fetch episodes when opening a scene
      if (!episodes[key]) {
        fetchEpisodes(scenarioId, sceneId);
      }
    }
  };

  const handleEpisodeClick = (scenarioId: string, sceneId: string, episodeId: string) => {
    // Use the custom video endpoint with proper headers
    const episodePath = `/video/${scenarioId}/${sceneId}/${episodeId}.mp4`;
    console.log('App: Episode clicked:', { scenarioId, sceneId, episodeId, episodePath });
    const newSelectedEpisode = {
      scenarioId,
      sceneId,
      episodeId,
      episodePath
    };
    console.log('App: Setting selectedEpisode to:', newSelectedEpisode);
    setSelectedEpisode(newSelectedEpisode);
  };

  return (
    <div className="app">
      {/* Header - Thin Blue Bar */}
      <header className="header">
        <div className="header-content">
          <h1 className="header-title">Botco Data Platform</h1>
        </div>
      </header>

      <div className="main-container">
        {/* Left Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-content">
            <h2 className="sidebar-title">Robotics Data</h2>
            
            <div className="dropdowns">
              {loading ? (
                <div className="loading">Loading scenarios...</div>
              ) : scenarios.length === 0 ? (
                <div className="loading">No scenarios found</div>
              ) : (
                scenarios.map((scenarioId) => (
                  <div key={scenarioId} className="dropdown">
                    <button
                      className="dropdown-header"
                      onClick={() => toggleScenario(scenarioId)}
                    >
                      <span>{scenarioId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                      <span className={`dropdown-arrow ${expandedScenario === scenarioId ? 'expanded' : ''}`}>
                        ▼
                      </span>
                    </button>
                    
                    {expandedScenario === scenarioId && (
                      <div className="dropdown-content">
                        {loadingScenes === scenarioId ? (
                          <div className="loading-subdirs">Loading scenes...</div>
                        ) : (
                          scenes[scenarioId]?.map((sceneId) => (
                            <div key={sceneId} className="nested-dropdown">
                              <button
                                className="scene-header"
                                onClick={() => toggleScene(scenarioId, sceneId)}
                              >
                                <span>{sceneId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                <span className={`dropdown-arrow ${expandedScene === `${scenarioId}-${sceneId}` ? 'expanded' : ''}`}>
                                  ▼
                                </span>
                              </button>
                              
                              {expandedScene === `${scenarioId}-${sceneId}` && (
                                <div className="episode-content">
                                  {loadingEpisodes === `${scenarioId}-${sceneId}` ? (
                                    <div className="loading-subdirs">Loading episodes...</div>
                                  ) : (
                                    episodes[`${scenarioId}-${sceneId}`]?.map((episodeId) => (
                                      <button
                                        key={episodeId}
                                        className="episode-button"
                                        onClick={() => handleEpisodeClick(scenarioId, sceneId, episodeId)}
                                      >
                                        {episodeId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                      </button>
                                    )) || []
                                  )}
                                </div>
                              )}
                            </div>
                          )) || []
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>

        {/* Main Dashboard */}
        <main className="dashboard">
          {selectedEpisode ? (
            <VideoPlayer
              episodePath={selectedEpisode.episodePath}
              episodeName={selectedEpisode.episodeId}
              scenarioName={selectedEpisode.scenarioId}
              sceneName={selectedEpisode.sceneId}
            />
          ) : (
            <div className="dashboard-content">
              <h1 className="dashboard-title">Botco</h1>
              <p className="dashboard-subtitle">Select an episode from the sidebar to start viewing</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;