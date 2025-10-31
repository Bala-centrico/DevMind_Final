/**
 * Real-time Task Monitor Component
 * Displays live progress of Jira automation tasks
 */
import React, { useState, useEffect } from 'react';
import { useWebSocket, TaskUpdate } from '../hooks/useWebSocket';
import './TaskMonitor.css';

interface TaskMonitorProps {
  jiraNumber: string;
  onClose?: () => void;
}

interface ProgressStage {
  name: string;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  message?: string;
  timestamp?: string;
}

const STAGES = [
  { key: 'analysis', label: 'Requirement Analysis' },
  { key: 'code_generation', label: 'Code Generation' },
  { key: 'testing', label: 'Testing & Validation' },
  { key: 'deployment', label: 'Deployment Preparation' }
];

export const TaskMonitor: React.FC<TaskMonitorProps> = ({ jiraNumber, onClose }) => {
  const [stages, setStages] = useState<Map<string, ProgressStage>>(
    new Map(STAGES.map(s => [s.key, { name: s.label, status: 'pending' }]))
  );
  const [currentProgress, setCurrentProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);

  const handleTaskUpdate = (update: TaskUpdate) => {
    if (update.jira_number !== jiraNumber) return;

    // Update stage status
    setStages(prev => {
      const newStages = new Map(prev);
      const stage = newStages.get(update.stage);
      if (stage) {
        newStages.set(update.stage, {
          ...stage,
          status: update.status as any,
          message: update.message,
          timestamp: update.timestamp
        });
      }
      return newStages;
    });

    // Update progress
    setCurrentProgress(update.progress);

    // Add to logs
    setLogs(prev => [...prev, `[${new Date(update.timestamp).toLocaleTimeString()}] ${update.message}`]);
  };

  const { isConnected, subscribeToTask } = useWebSocket({
    url: 'ws://localhost:5002/ws/monitor',
    onTaskUpdate: handleTaskUpdate
  });

  useEffect(() => {
    if (isConnected) {
      subscribeToTask(jiraNumber);
    }
  }, [isConnected, jiraNumber, subscribeToTask]);

  return (
    <div className="task-monitor">
      <div className="monitor-header">
        <h2>Monitoring: {jiraNumber}</h2>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
          {isConnected ? 'Connected' : 'Connecting...'}
        </div>
        {onClose && (
          <button className="close-btn" onClick={onClose}>×</button>
        )}
      </div>

      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${currentProgress}%` }}
          />
        </div>
        <span className="progress-text">{currentProgress}%</span>
      </div>

      <div className="stages-container">
        {STAGES.map(stage => {
          const stageData = stages.get(stage.key);
          return (
            <div key={stage.key} className={`stage stage-${stageData?.status}`}>
              <div className="stage-icon">
                {stageData?.status === 'completed' && '✓'}
                {stageData?.status === 'in-progress' && '⟳'}
                {stageData?.status === 'error' && '✗'}
                {stageData?.status === 'pending' && '○'}
              </div>
              <div className="stage-content">
                <h3>{stage.label}</h3>
                {stageData?.message && <p>{stageData.message}</p>}
                {stageData?.timestamp && (
                  <span className="timestamp">
                    {new Date(stageData.timestamp).toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="logs-container">
        <h3>Activity Log</h3>
        <div className="logs">
          {logs.length === 0 ? (
            <p className="no-logs">Waiting for updates...</p>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="log-entry">{log}</div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
