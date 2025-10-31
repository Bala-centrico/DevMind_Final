import React from 'react';
import './ErrorNotification.css';

interface ErrorNotificationProps {
  message: string;
  onClose: () => void;
}

const ErrorNotification: React.FC<ErrorNotificationProps> = ({ message, onClose }) => {
  return (
    <div className="error-notification">
      <div className="error-content">
        <span className="error-icon">❌</span>
        <span className="error-message">{message}</span>
        <button className="error-close-btn" onClick={onClose}>
          ✕
        </button>
      </div>
    </div>
  );
};

export default ErrorNotification;