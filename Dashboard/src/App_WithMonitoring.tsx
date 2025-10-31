/**
 * Updated App.tsx with Real-Time Monitoring Integration
 */
import React, { useState, useEffect } from 'react';
import './App.css';
import { StatsCard, TaskCard, TaskMonitor } from './components';
import { Task, DashboardStats } from './types';

// API Configuration
const MONITORING_API = 'http://localhost:5002';

const App: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalTasks: 0,
    automationReady: 0,
    inProgress: 0,
    completed: 0,
    highPriority: 0
  });
  const [monitoringTask, setMonitoringTask] = useState<number | null>(null);
  const [isMonitoringAvailable, setIsMonitoringAvailable] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check monitoring service availability
  useEffect(() => {
    const checkMonitoringService = async () => {
      try {
        const response = await fetch(`${MONITORING_API}/api/health`);
        if (response.ok) {
          setIsMonitoringAvailable(true);
        }
      } catch (error) {
        console.warn('Monitoring service not available:', error);
        setIsMonitoringAvailable(false);
      }
    };

    checkMonitoringService();
    const interval = setInterval(checkMonitoringService, 30000); // Check every 30s

    return () => clearInterval(interval);
  }, []);

  // Fetch tasks from monitoring service
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${MONITORING_API}/api/tasks`);
        if (response.ok) {
          const data = await response.json();
          
          // Transform database format to UI format
          const transformedTasks: Task[] = data.tasks.map((task: any) => ({
            id: task.jira_number,
            title: task.jira_heading || 'No description',
            assignee: task.assignee || 'Unassigned',
            createdDate: task.created || '',
            updatedDate: task.last_updated || '',
            tags: [],
            status: task.status || 'Open',
            descriptionClarity: task.requirement_clarity || 'Medium',
            automationEligible: task.automation === 'Yes',
            priority: task.priority || 'Medium',
            taskStatus: task.status || 'Open'
          }));

          setTasks(transformedTasks);

          // Calculate stats
          const newStats: DashboardStats = {
            totalTasks: transformedTasks.length,
            automationReady: transformedTasks.filter(t => t.automationEligible).length,
            inProgress: transformedTasks.filter(t => t.status === 'In Progress').length,
            completed: transformedTasks.filter(t => t.status === 'Done' || t.taskStatus === 'Completed').length,
            highPriority: transformedTasks.filter(t => t.priority === 'High').length
          };
          setStats(newStats);
        }
      } catch (error) {
        console.error('Error fetching tasks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
    
    // Refresh tasks every 10 seconds
    const interval = setInterval(fetchTasks, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (jiraId: string) => {
    console.log('Analyze clicked for:', jiraId);
    
    // TODO: Call your analysis API
    try {
      const response = await fetch(`${MONITORING_API}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jira_number: jiraId })
      });
      
      if (response.ok) {
        // Refresh tasks after analysis
        console.log('Analysis started for', jiraId);
      }
    } catch (error) {
      console.error('Error triggering analysis:', error);
    }
  };

  const handleDeploy = (taskId: number) => {
    console.log('Deploy clicked for task ID:', taskId);
    
    // Find the task to get its jira_number
    const task = tasks.find(t => t.id === taskId);
    if (task) {
      setMonitoringTask(taskId);
      
      // TODO: Call your deployment API
      // fetch(`${MONITORING_API}/api/deploy`, { ... })
    }
  };

  return (
    <div className="App">
      {/* Monitoring Service Status Banner */}
      <div className={`info-banner ${isMonitoringAvailable ? 'success' : 'warning'}`}>
        <span className="info-icon">{isMonitoringAvailable ? '✓' : 'ℹ️'}</span>
        <span>
          {isMonitoringAvailable ? (
            <>
              <strong>Monitoring Active:</strong> Real-time progress tracking enabled on port 5002
            </>
          ) : (
            <>
              <strong>Monitoring Offline:</strong> Start monitoring service to enable real-time tracking
            </>
          )}
        </span>
      </div>

      {/* Connection Status Banner */}
      <div className="info-banner">
        <span className="info-icon">ℹ️</span>
        <span>
          <strong>VSCode Integration:</strong> Make sure your VSCode extension is running on localhost:8765 to enable automation features.
        </span>
      </div>

      {/* Stats Section */}
      <div className="stats-section">
        <StatsCard title="Total Tasks" value={stats.totalTasks} color="blue" />
        <StatsCard title="Automation Ready" value={stats.automationReady} color="green" />
        <StatsCard title="In Progress" value={stats.inProgress} color="orange" />
        <StatsCard title="Completed" value={stats.completed} color="teal" />
        <StatsCard title="High Priority" value={stats.highPriority} color="red" />
      </div>

      {/* Tasks Section */}
      {loading ? (
        <div className="loading">Loading tasks...</div>
      ) : tasks.length === 0 ? (
        <div className="no-tasks">No tasks available</div>
      ) : (
        <div className="tasks-section">
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onAnalyze={handleAnalyze}
              onDeploy={handleDeploy}
            />
          ))}
        </div>
      )}

      {/* Monitoring Modal */}
      {monitoringTask && (
        <div className="modal-overlay">
          <TaskMonitor
            jiraNumber={tasks.find(t => t.id === monitoringTask)?.jira_number || ''}
            onClose={() => setMonitoringTask(null)}
          />
        </div>
      )}
    </div>
  );
}

export default App;
