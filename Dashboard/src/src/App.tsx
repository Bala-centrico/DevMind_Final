import React, { useState, useEffect } from 'react';
import './App.css';
import { StatsCard, TaskCard, ThemeToggle, ErrorNotification } from './components';
import { Task, DashboardStats } from './types';
import { ThemeProvider } from './contexts/ThemeContext';

// API Response interfaces
interface JiraApiResponse {
  success: boolean;
  message: string;
  data: Task[];
  total_count: number;
  timestamp: string;
}

interface AnalyzeApiResponse {
  isValidJiraId: boolean;
  isPromptInjectVScode: boolean;
  genratedPrompt: string;
  error: string | null;
}

const App: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState<boolean>(true);
  const [refreshInterval, setRefreshInterval] = useState<number>(30); // seconds
  const [analyzingTasks, setAnalyzingTasks] = useState<Set<string>>(new Set());
  const [apiError, setApiError] = useState<string | null>(null);
  const tasksPerPage = 10;

  // Fetch JIRA data from API
  const fetchJiraData = async (isBackground = false) => {
    try {
      if (!isBackground) {
        setLoading(true);
      }
      setError(null);
      
      const response = await fetch('http://localhost:8001/api/v1/jiraCards');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const apiResponse: JiraApiResponse = await response.json();
      
      if (apiResponse.success) {
        setTasks(apiResponse.data);
        setLastUpdated(apiResponse.timestamp);
        if (!isBackground) {
          console.log(`✅ Successfully loaded ${apiResponse.total_count} JIRA tasks`);
        }
      } else {
        throw new Error(apiResponse.message || 'Failed to fetch JIRA data');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('❌ Failed to fetch JIRA data:', errorMessage);
    } finally {
      if (!isBackground) {
        setLoading(false);
      }
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchJiraData();
  }, []);

  // Auto-refresh functionality
  useEffect(() => {
    if (!isAutoRefreshEnabled) return;

    const interval = setInterval(() => {
      fetchJiraData(true); // Background fetch
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [isAutoRefreshEnabled, refreshInterval]);

  // Calculate stats based on fetched data
  const stats: DashboardStats = {
    totalTasks: tasks.length,
    automationReady: tasks.filter(task => task.automation === 'Ready').length,
    inProgress: tasks.filter(task => task.status === 'In Progress').length,
    completed: tasks.filter(task => task.status === 'Completed').length,
    highPriority: tasks.filter(task => task.priority === 'High').length
  };

  // Pagination logic
  const totalPages = Math.ceil(tasks.length / tasksPerPage);
  const startIndex = (currentPage - 1) * tasksPerPage;
  const endIndex = startIndex + tasksPerPage;
  const currentTasks = tasks.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // Scroll to top when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      handlePageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      handlePageChange(currentPage + 1);
    }
  };

  // Analyze functionality
  const handleAnalyze = async (jiraId: string) => {
    try {
      setAnalyzingTasks(prev => new Set(prev).add(jiraId));
      setApiError(null);
      
      const response = await fetch('http://localhost:8001/api/v1/injectAndSavePrompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ jira_id: jiraId })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const apiResponse: AnalyzeApiResponse = await response.json();
      
      if (apiResponse.error) {
        setApiError(apiResponse.error);
      } else {
        console.log(`✅ Analysis completed for ${jiraId}`);
        // Refresh data to get updated status
        await fetchJiraData(true);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred during analysis';
      setApiError(`Failed to analyze ${jiraId}: ${errorMessage}`);
      console.error('❌ Failed to analyze task:', errorMessage);
    } finally {
      setAnalyzingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(jiraId);
        return newSet;
      });
    }
  };

  const handleDeploy = (taskId: number) => {
    console.log(`🚀 Deploy triggered for task: ${taskId}`);
    // Add deployment logic here
  };

  const handleCodeApproval = async (taskId: number, approved: boolean, comment?: string) => {
    try {
      const task = tasks.find(t => t.id === taskId);
      if (!task) return;

      // Update the task's decision status locally
      setTasks(prevTasks => 
        prevTasks.map(t => 
          t.id === taskId 
            ? { 
                ...t, 
                decision: approved ? 'Approved' : 'Rejected',
                comment: comment || t.comment 
              }
            : t
        )
      );

      console.log(`${approved ? '✅ Approved' : '❌ Rejected'} code for task ${task.jira_number}${comment ? ` - ${comment}` : ''}`);
      
      // Here you would typically call an API to update the decision in the backend
      // await updateTaskDecision(taskId, approved, comment);
      
    } catch (err) {
      console.error('Failed to update code approval:', err);
      setApiError('Failed to update code approval status');
    }
  };

  const handleRefresh = () => {
    setCurrentPage(1);
    fetchJiraData();
  };

  const toggleAutoRefresh = () => {
    setIsAutoRefreshEnabled(!isAutoRefreshEnabled);
  };

  const handleIntervalChange = (interval: number) => {
    setRefreshInterval(interval);
  };

  // Loading state
  if (loading) {
    return (
      <ThemeProvider>
        <div className="App">
          <div className="loading-container">
            <div className="loading-spinner">🤖</div>
            <h2>Loading JIRA Tasks...</h2>
            <p>Fetching data from AI-powered backend...</p>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  // Error state
  if (error) {
    return (
      <ThemeProvider>
        <div className="App">
          <div className="error-container">
            <div className="error-icon">❌</div>
            <h2>Failed to Load JIRA Data</h2>
            <p className="error-message">{error}</p>
            <p className="error-suggestion">
              Please ensure the API server is running at <code>http://localhost:8001</code>
            </p>
            <button className="btn btn-primary" onClick={handleRefresh}>
              🔄 Retry
            </button>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <div className="App">
        {/* AI-Enhanced Header */}
        <header className="app-header">
          <div className="header-content">
            <div className="header-text">
              <h1 className="app-title">
                🤖 DevMind Dashboard
              </h1>
              <p className="app-subtitle">
               
              </p>
              {lastUpdated && (
                <div className="last-updated">
                  🕒 Last updated: {new Date(lastUpdated).toLocaleString()}
                </div>
              )}
            </div>
            <div className="header-controls-top">
              <ThemeToggle />
            </div>
          </div>
        </header>

      {/* Stats Section */}
      <div className="stats-section">
        <StatsCard title="Total Tasks" value={stats.totalTasks} color="blue" />
        <StatsCard title="AI Analyzed" value={tasks.filter(t => t.requirement_clarity || t.automation).length} color="blue" />
        <StatsCard title="Pending Analysis" value={tasks.filter(t => !t.requirement_clarity && !t.automation).length} color="orange" />
        <StatsCard title="Completed" value={stats.completed} color="green" />
        <StatsCard title="High Priority" value={stats.highPriority} color="red" />
      </div>

      {/* Tasks Section */}
      <div className="tasks-section">
        <div className="section-header">
          <h2 className="section-title">
            📋 JIRA Tasks ({tasks.length})
          </h2>
          <div className="header-controls">
            {tasks.length > 0 && (
              <div className="pagination-info">
                Page {currentPage} of {totalPages} • Showing {currentTasks.length} of {tasks.length} tasks
              </div>
            )}
            
            {/* Auto-refresh controls */}
            <div className="auto-refresh-controls">
              <label className="refresh-toggle">
                <input
                  type="checkbox"
                  checked={isAutoRefreshEnabled}
                  onChange={toggleAutoRefresh}
                />
                Auto-refresh
              </label>
              
              {isAutoRefreshEnabled && (
                <select 
                  value={refreshInterval} 
                  onChange={(e) => handleIntervalChange(Number(e.target.value))}
                  className="refresh-interval-select"
                >
                  <option value={10}>10s</option>
                  <option value={30}>30s</option>
                  <option value={60}>1m</option>
                  <option value={300}>5m</option>
                </select>
              )}
            </div>
            
            <button className="btn btn-secondary refresh-btn" onClick={handleRefresh}>
              🔄 Refresh
            </button>
          </div>
        </div>
        
        {tasks.length === 0 ? (
          <div className="no-tasks">
            <div className="no-tasks-icon">📝</div>
            <h3>No JIRA Tasks Found</h3>
            <p>The API returned no tasks. Please check your JIRA integration.</p>
          </div>
        ) : (
          <>
            {currentTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onAnalyze={handleAnalyze}
                onDeploy={() => handleDeploy(task.id)}
                isAnalyzing={analyzingTasks.has(task.jira_number)}
                onCodeApproval={handleCodeApproval}
              />
            ))}
            
            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="pagination-controls">
                <button 
                  className={`btn btn-pagination ${currentPage === 1 ? 'disabled' : ''}`}
                  onClick={handlePrevPage}
                  disabled={currentPage === 1}
                >
                  ← Previous
                </button>
                
                <div className="pagination-numbers">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                    <button
                      key={page}
                      className={`btn btn-page ${currentPage === page ? 'active' : ''}`}
                      onClick={() => handlePageChange(page)}
                    >
                      {page}
                    </button>
                  ))}
                </div>
                
                <button 
                  className={`btn btn-pagination ${currentPage === totalPages ? 'disabled' : ''}`}
                  onClick={handleNextPage}
                  disabled={currentPage === totalPages}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>
      </div>
      
      {/* Error Notification */}
      {apiError && (
        <ErrorNotification 
          message={apiError} 
          onClose={() => setApiError(null)} 
        />
      )}
    </ThemeProvider>
  );
}

export default App;