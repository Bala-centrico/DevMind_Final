import React, { useEffect, useState } from 'react';
import './ProgressMonitor.css';

interface ProgressUpdate {
  jiraNumber: string;
  stage: string;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  message: string;
  progress: number;
  timestamp: string;
}

interface ProgressMonitorProps {
  jiraNumber: string;
  onClose: () => void;
  onComplete?: () => void; // Callback to refresh tasks when analysis completes
}

const ProgressMonitor: React.FC<ProgressMonitorProps> = ({ jiraNumber, onClose, onComplete }) => {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Connect to monitoring WebSocket
    const websocket = new WebSocket(`ws://localhost:5002/ws/monitor/${jiraNumber}`);
    
    websocket.onopen = () => {
      console.log(`✅ Connected to monitor for ${jiraNumber}`);
      setIsConnected(true);
    };
    
    websocket.onmessage = (event) => {
      const update: ProgressUpdate = JSON.parse(event.data);
      console.log('Progress update:', update);
      setProgress(update);
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket closed');
      setIsConnected(false);
    };
    
    setWs(websocket);
    
    // Cleanup
    return () => {
      websocket.close();
    };
  }, [jiraNumber]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'in-progress': return '🔄';
      case 'error': return '❌';
      default: return '⏳';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'in-progress': return 'blue';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div className="progress-monitor-overlay">
      <div className="progress-monitor">
        <div className="progress-header">
          <h2>Analyzing {jiraNumber}</h2>
          <div className="connection-status">
            <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
            {isConnected ? 'Live' : 'Connecting...'}
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {progress && (
          <>
            <div className="progress-bar-container">
              <div className="progress-bar">
                <div 
                  className={`progress-fill ${progress.status}`}
                  style={{ width: `${progress.progress}%` }}
                />
              </div>
              <div className="progress-text">{progress.progress}%</div>
            </div>

            <div className="current-stage">
              <span className="stage-icon">{getStatusIcon(progress.status)}</span>
              <div className="stage-details">
                <h3>{progress.message}</h3>
                <p className="timestamp">
                  {new Date(progress.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>

            <div className="stages-list">
              <div className={`stage-item ${progress.progress >= 10 ? 'completed' : 'pending'}`}>
                <span className="stage-number">1</span>
                <span className="stage-label">Prompt Injected</span>
              </div>
              <div className={`stage-item ${progress.progress >= 25 ? 'completed' : progress.progress >= 10 ? 'active' : 'pending'}`}>
                <span className="stage-number">2</span>
                <span className="stage-label">Fetching Jira</span>
              </div>
              <div className={`stage-item ${progress.progress >= 40 ? 'completed' : progress.progress >= 25 ? 'active' : 'pending'}`}>
                <span className="stage-number">3</span>
                <span className="stage-label">Analyzing Standards</span>
              </div>
              <div className={`stage-item ${progress.progress >= 55 ? 'completed' : progress.progress >= 40 ? 'active' : 'pending'}`}>
                <span className="stage-number">4</span>
                <span className="stage-label">Searching Past Work</span>
              </div>
              <div className={`stage-item ${progress.progress >= 70 ? 'completed' : progress.progress >= 55 ? 'active' : 'pending'}`}>
                <span className="stage-number">5</span>
                <span className="stage-label">Analyzing SVN Code</span>
              </div>
              <div className={`stage-item ${progress.progress >= 90 ? 'completed' : progress.progress >= 70 ? 'active' : 'pending'}`}>
                <span className="stage-number">6</span>
                <span className="stage-label">Generating Code</span>
              </div>
              <div className={`stage-item ${progress.progress >= 95 ? 'completed' : progress.progress >= 90 ? 'active' : 'pending'}`}>
                <span className="stage-number">7</span>
                <span className="stage-label">Testing Code</span>
              </div>
              <div className={`stage-item ${progress.progress === 100 ? 'completed' : progress.progress >= 95 ? 'active' : 'pending'}`}>
                <span className="stage-number">8</span>
                <span className="stage-label">Saving Results</span>
              </div>
            </div>

            {progress.status === 'completed' && progress.progress === 100 && (
              <div className="completion-message">
                <h3>✅ Analysis Complete!</h3>
                <p>Code is ready for review. Close this window to see the results.</p>
                <button className="btn btn-primary" onClick={() => {
                  onComplete?.(); // Refresh tasks to show generated code
                  onClose(); // Close modal
                }}>
                  View Generated Code
                </button>
              </div>
            )}

            {progress.status === 'error' && (
              <div className="error-message">
                <h3>❌ Error Occurred</h3>
                <p>{progress.message}</p>
                <button className="btn btn-secondary" onClick={onClose}>
                  Close
                </button>
              </div>
            )}
          </>
        )}

        {!progress && isConnected && (
          <div className="waiting-message">
            <div className="spinner">🔄</div>
            <p>Waiting for progress updates...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressMonitor;
