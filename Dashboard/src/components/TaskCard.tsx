import React, { useState } from 'react';
import { Task } from '../types';
import './TaskCard.css';

interface TaskCardProps {
  task: Task;
  onAnalyze?: (jiraId: string) => Promise<void>;
  onDeploy?: (taskId: number) => void;
  isAnalyzing?: boolean;
  onCodeApproval?: (taskId: number, approved: boolean, comment?: string) => void;
}

const TaskCard: React.FC<TaskCardProps> = ({ 
  task, 
  onAnalyze, 
  onDeploy, 
  isAnalyzing = false,
  onCodeApproval 
}) => {
  const [showCodeModal, setShowCodeModal] = useState(false);
  const [rejectionComment, setRejectionComment] = useState('');
  const [showRejectionModal, setShowRejectionModal] = useState(false);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getTypeIcon = (type: string | null) => {
    if (!type) return '📋';
    switch (type.toLowerCase()) {
      case 'story':
        return '📖';
      case 'improvement':
        return '⚡';
      case 'bug':
        return '🐛';
      case 'task':
        return '✅';
      default:
        return '📋';
    }
  };

  const getDecisionIcon = (decision: string | null) => {
    if (!decision) return '❓';
    switch (decision.toLowerCase()) {
      case 'approved':
        return '✅';
      case 'rejected':
        return '❌';
      case 'pending':
        return '⏳';
      default:
        return '❓';
    }
  };

  const getAnalysisStatus = () => {
    if (task.gen_code && task.gen_test_case) {
      return { status: 'Analysis Complete', icon: '✅', color: 'completed' };
    } else if (isAnalyzing) {
      return { status: 'Analyzing...', icon: '🔄', color: 'analyzing' };
    } else if (task.requirement_clarity) {
      return { status: 'Partial Analysis', icon: '🔍', color: 'partial' };
    } else {
      return { status: 'Pending Analysis', icon: '🧠', color: 'pending' };
    }
  };

  const analysisStatus = getAnalysisStatus();
  const hasGeneratedCode = !!(task.gen_code && task.gen_test_case);
  const isDeployEnabled = hasGeneratedCode && task.decision?.toLowerCase() === 'approved';

  const handleAnalyzeClick = async () => {
    if (onAnalyze && !isAnalyzing) {
      await onAnalyze(task.jira_number);
    }
  };

  const handleDeployClick = () => {
    if (onDeploy && isDeployEnabled) {
      onDeploy(task.id);
    }
  };

  const handleViewCode = () => {
    if (hasGeneratedCode) {
      setShowCodeModal(true);
    }
  };

  const handleApproveCode = () => {
    if (onCodeApproval) {
      onCodeApproval(task.id, true);
    }
    setShowCodeModal(false);
  };

  const handleRejectCode = () => {
    setShowRejectionModal(true);
  };

  const handleConfirmRejection = () => {
    if (onCodeApproval) {
      onCodeApproval(task.id, false, rejectionComment);
    }
    setShowRejectionModal(false);
    setShowCodeModal(false);
    setRejectionComment('');
  };

  const renderCodeModal = () => {
    if (!showCodeModal || !hasGeneratedCode) return null;

    return (
      <div className="code-modal-overlay" onClick={() => setShowCodeModal(false)}>
        <div className="code-modal" onClick={(e) => e.stopPropagation()}>
          <div className="code-modal-header">
            <h3>Generated Code - {task.jira_number}</h3>
            <button 
              className="close-btn"
              onClick={() => setShowCodeModal(false)}
            >
              ✕
            </button>
          </div>
          
          <div className="code-modal-content">
            <div className="code-section">
              <h4>📝 Generated Code</h4>
              <pre className="code-display">
                <code>{task.gen_code}</code>
              </pre>
            </div>
            
            <div className="code-section">
              <h4>🧪 Test Case</h4>
              <pre className="code-display">
                <code>{task.gen_test_case}</code>
              </pre>
            </div>
          </div>
          
          <div className="code-modal-actions">
            <button 
              className="btn btn-success"
              onClick={handleApproveCode}
            >
              ✅ Approve Code
            </button>
            <button 
              className="btn btn-danger"
              onClick={handleRejectCode}
            >
              ❌ Reject Code
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderRejectionModal = () => {
    if (!showRejectionModal) return null;

    return (
      <div className="code-modal-overlay" onClick={() => setShowRejectionModal(false)}>
        <div className="rejection-modal" onClick={(e) => e.stopPropagation()}>
          <div className="code-modal-header">
            <h3>Reject Code - {task.jira_number}</h3>
            <button 
              className="close-btn"
              onClick={() => setShowRejectionModal(false)}
            >
              ✕
            </button>
          </div>
          
          <div className="rejection-modal-content">
            <label htmlFor="rejection-comment">Please provide a reason for rejection:</label>
            <textarea
              id="rejection-comment"
              value={rejectionComment}
              onChange={(e) => setRejectionComment(e.target.value)}
              placeholder="Enter reason for rejecting the generated code..."
              rows={4}
              required
            />
          </div>
          
          <div className="code-modal-actions">
            <button 
              className="btn btn-secondary"
              onClick={() => setShowRejectionModal(false)}
            >
              Cancel
            </button>
            <button 
              className="btn btn-danger"
              onClick={handleConfirmRejection}
              disabled={!rejectionComment.trim()}
            >
              Confirm Rejection
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      <div className="task-card">
        <div className="task-header">
          <div className="task-number-section">
            <h3 className="task-id">{task.jira_number}</h3>
            <span className="task-type">
              {getTypeIcon(task.type)} {task.type || 'Unknown'}
            </span>
          </div>
          <div className="task-badges">
            <span className={`badge priority-${(task.priority || 'medium').toLowerCase()}`}>
              {task.priority || 'Medium'}
            </span>
            <span className={`badge status-${(task.status || 'unknown').toLowerCase().replace(' ', '-')}`}>
              {task.status || 'Unknown'}
            </span>
          </div>
        </div>

        <p className="task-title">{task.jira_heading}</p>

        <div className="task-meta">
          <div className="task-meta-item">
            <span className="icon">👤</span>
            <span>{task.assignee || 'Unassigned'}</span>
          </div>
          <div className="task-meta-item">
            <span className="icon">📅</span>
            <span>Created: {formatDate(task.created)}</span>
          </div>
          <div className="task-meta-item">
            <span className="icon">🕒</span>
            <span>Updated: {formatDate(task.last_updated)}</span>
          </div>
        </div>

        <div className="ai-analysis-section">
          <div className="ai-status">
            <span className={`ai-badge ${analysisStatus.color}`}>
              <span className={isAnalyzing ? 'spinner' : ''}>{analysisStatus.icon}</span>
              {analysisStatus.status}
            </span>
          </div>
          
          {task.requirement_clarity && (
            <div className="info-item">
              <span className="info-label">🎯 Requirement Clarity:</span>
              <span className={`info-value clarity-${task.requirement_clarity.toLowerCase()}`}>
                {task.requirement_clarity}
              </span>
            </div>
          )}
          
          {task.automation && (
            <div className="info-item">
              <span className="info-label">⚙️ Automation Assessment:</span>
              <span className="info-value automation">
                {task.automation}
              </span>
            </div>
          )}

          <div className="info-item">
            <span className="info-label">🎯 Decision:</span>
            <span className={`info-value decision-${(task.decision || 'unknown').toLowerCase()}`}>
              {getDecisionIcon(task.decision)} {task.decision || 'Unknown'}
            </span>
          </div>

          {task.comment && (
            <div className="info-item">
              <span className="info-label">💬 AI Comment:</span>
              <span className="info-value comment">
                {task.comment}
              </span>
            </div>
          )}

          {hasGeneratedCode && (
            <div className="code-generation-section">
              <div className="code-status">
                <span className="code-ready-badge">
                  📝 Code Generated
                </span>
                <button 
                  className="btn btn-view-code"
                  onClick={handleViewCode}
                >
                  👁️ View Code
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="task-actions">
          <button 
            className={`btn btn-tertiary ${isAnalyzing ? 'analyzing' : ''}`}
            onClick={handleAnalyzeClick}
            disabled={isAnalyzing || hasGeneratedCode}
          >
            <span className={`icon ${isAnalyzing ? 'spinner' : ''}`}>
              {isAnalyzing ? '🔄' : '🧠'}
            </span>
            {isAnalyzing ? 'Analyzing...' : hasGeneratedCode ? 'Analyzed' : 'Analyze'}
          </button>
          
          <button 
            className={`btn btn-primary ${!isDeployEnabled ? 'disabled' : ''}`}
            onClick={handleDeployClick}
            disabled={!isDeployEnabled}
            title={!hasGeneratedCode ? 'Complete analysis first' : !isDeployEnabled ? 'Approve code to enable deploy' : 'Deploy to production'}
          >
            <span className="icon">🚀</span>
            Deploy
          </button>
        </div>
      </div>

      {renderCodeModal()}
      {renderRejectionModal()}
    </>
  );
};

export default TaskCard;
