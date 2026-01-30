import React from 'react';
import { GlassCard } from './GlassCard';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    positive: boolean;
  };
  className?: string;
  style?: React.CSSProperties;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  trend,
  className = '',
  style,
}) => {
  return (
    <GlassCard className={`stat-card ${className}`} hover style={style}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="stat-label">{label}</p>
          <p className="stat-value">{value}</p>
          {trend && (
            <div className={`flex items-center gap-1 text-sm font-medium ${
              trend.positive ? 'text-accent-green' : 'text-accent-pink'
            }`}>
              <span>{trend.positive ? '↑' : '↓'}</span>
              <span>{trend.value}</span>
            </div>
          )}
        </div>
        {icon && (
          <div className="text-4xl opacity-20">
            {icon}
          </div>
        )}
      </div>
    </GlassCard>
  );
};
