import { useState, useEffect, useCallback } from 'react';
import { Task } from '../types';

interface JiraApiResponse {
  success: boolean;
  message: string;
  data: Task[];
  total_count: number;
  timestamp: string;
}

interface UseJiraDataOptions {
  autoRefreshInterval?: number;
  autoRefreshEnabled?: boolean;
}

export const useJiraData = (options: UseJiraDataOptions = {}) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const fetchJiraData = useCallback(async (isBackground = false) => {
    try {
      if (!isBackground) {
        setLoading(true);
      } else {
        setIsRefreshing(true);
      }
      setError(null);
      
      const response = await fetch('http://localhost:8001/api/v1/jiraCards', {
        // Add cache headers to ensure fresh data
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const apiResponse: JiraApiResponse = await response.json();
      
      if (apiResponse.success) {
        setTasks(apiResponse.data);
        setLastUpdated(apiResponse.timestamp);
        if (!isBackground) {
          console.log(`✅ Successfully loaded ${apiResponse.total_count} JIRA tasks`);
        } else {
          console.log(`🔄 Background refresh: ${apiResponse.total_count} tasks updated`);
        }
      } else {
        throw new Error(apiResponse.message || 'Failed to fetch JIRA data');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('❌ Failed to fetch JIRA data:', errorMessage);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchJiraData();
  }, [fetchJiraData]);

  // Auto-refresh functionality
  useEffect(() => {
    if (!options.autoRefreshEnabled || !options.autoRefreshInterval) return;

    const interval = setInterval(() => {
      fetchJiraData(true); // Background fetch
    }, options.autoRefreshInterval * 1000);

    return () => clearInterval(interval);
  }, [options.autoRefreshEnabled, options.autoRefreshInterval, fetchJiraData]);

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchJiraData();
  }, [fetchJiraData]);

  return {
    tasks,
    loading,
    error,
    lastUpdated,
    isRefreshing,
    refresh
  };
};