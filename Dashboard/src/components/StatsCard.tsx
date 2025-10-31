import React from 'react';
import './StatsCard.css';

interface StatsCardProps {
  title: string;
  value: number;
  color: 'blue' | 'green' | 'orange' | 'teal' | 'red';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, color }) => {
  return (
    <div className="stats-card">
      <div className={`stats-value ${color}`}>{value}</div>
      <div className="stats-title">{title}</div>
    </div>
  );
};

export default StatsCard;
