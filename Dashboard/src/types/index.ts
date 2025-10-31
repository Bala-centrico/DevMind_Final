export interface Task {
  id: number;
  jira_number: string;
  jira_heading: string | null;
  assignee: string | null;
  created: string;
  priority: 'High' | 'Medium' | 'Low' | null;
  type: string | null;
  requirement_clarity: string | null;
  automation: string | null;
  comment: string | null;
  decision: string | null;
  last_updated: string;
  status: string | null;
  // Additional UI properties
  automationEligible?: boolean;
  taskStatus?: string;
  // New fields from jira_prompts table
  prompt_id?: number | null;
  category?: string | null;
  analysis_prompt?: string | null;
  gen_code?: string | null;
  gen_test_case?: string | null;
  deployment_prompt?: string | null;
  rewards?: number | null;
}

export interface DashboardStats {
  totalTasks: number;
  automationReady: number;
  inProgress: number;
  completed: number;
  highPriority: number;
}

export type Theme = 'light' | 'dark';

export interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}