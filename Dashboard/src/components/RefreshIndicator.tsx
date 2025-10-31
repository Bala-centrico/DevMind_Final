import React from 'react';
import './RefreshIndicator.css';

interface RefreshIndicatorProps {
  isRefreshing: boolean;
  lastUpdated: string;
  autoRefreshEnabled: boolean;
  refreshInterval: number;
  onToggleAutoRefresh: () => void;
  onIntervalChange: (interval: number) => void;
  onManualRefresh: () => void;
}

const RefreshIndicator: React.FC<RefreshIndicatorProps> = ({
  isRefreshing,
  lastUpdated,
  autoRefreshEnabled,
  refreshInterval,
  onToggleAutoRefresh,
  onIntervalChange,
  onManualRefresh
}) => {
  const formatLastUpdated = (timestamp: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    return date.toLocaleTimeString();
  };

  return (
    <div className="refresh-indicator">
      <div className="refresh-status">
        {isRefreshing ? (
          <span className="refreshing">
            <span className="spinner">🔄</span>
            Updating...
          </span>
        ) : (
          <span className="last-updated">
            🕒 Updated {formatLastUpdated(lastUpdated)}
          </span>
        )}
      </div>

      <div className="refresh-controls">
        <label className="auto-refresh-toggle">
          <input
            type="checkbox"
            checked={autoRefreshEnabled}
            onChange={onToggleAutoRefresh}
          />
          <span className="toggle-text">Auto-refresh</span>
        </label>

        {autoRefreshEnabled && (
          <select 
            value={refreshInterval} 
            onChange={(e) => onIntervalChange(Number(e.target.value))}
            className="interval-select"
            disabled={isRefreshing}
          >
            <option value={10}>10s</option>
            <option value={30}>30s</option>
            <option value={60}>1m</option>
            <option value={300}>5m</option>
            <option value={900}>15m</option>
          </select>
        )}

        <button 
          className={`refresh-btn ${isRefreshing ? 'refreshing' : ''}`}
          onClick={onManualRefresh}
          disabled={isRefreshing}
        >
          <span className={isRefreshing ? 'spinner' : ''}>🔄</span>
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
    </div>
  );
};

export default RefreshIndicator;