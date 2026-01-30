/**
 * ProgressCard Component - Fitness App Style
 * Circular and arc progress gauges with vibrant colors
 */

import React from 'react';
import { clsx } from 'clsx';

interface ProgressCardProps {
  label: string;
  value: number;
  maxValue?: number;
  unit?: string;
  type?: 'circular' | 'arc' | 'linear';
  color?: 'purple' | 'green' | 'lime' | 'blue' | 'pink' | 'yellow' | 'red';
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
  icon?: React.ReactNode;
  subtitle?: string;
  className?: string;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({
  label,
  value,
  maxValue = 100,
  unit = '',
  type = 'circular',
  color = 'purple',
  size = 'md',
  showPercentage = true,
  icon,
  subtitle,
  className = '',
}) => {
  const percentage = Math.min((value / maxValue) * 100, 100);
  
  const colorClasses = {
    purple: {
      bg: 'from-brand-purple-500 to-brand-purple-600',
      glow: 'shadow-glow-purple',
      text: 'text-brand-purple-400',
      gradient: { start: '#A855F7', end: '#9333EA' },
    },
    green: {
      bg: 'from-accent-green-400 to-accent-green-600',
      glow: 'shadow-glow-green',
      text: 'text-accent-green-400',
      gradient: { start: '#10B981', end: '#059669' },
    },
    lime: {
      bg: 'from-accent-lime-400 to-accent-lime-600',
      glow: 'shadow-glow-lime',
      text: 'text-accent-lime-400',
      gradient: { start: '#CAFF00', end: '#A3CC00' },
    },
    blue: {
      bg: 'from-accent-blue-400 to-accent-blue-600',
      glow: 'shadow-glow-blue',
      text: 'text-accent-blue-400',
      gradient: { start: '#3B82F6', end: '#2563EB' },
    },
    pink: {
      bg: 'from-accent-pink-400 to-accent-pink-600',
      glow: 'shadow-glow-pink',
      text: 'text-accent-pink-400',
      gradient: { start: '#EC4899', end: '#DB2777' },
    },
    yellow: {
      bg: 'from-accent-yellow-400 to-accent-yellow-600',
      glow: 'shadow-glow-yellow',
      text: 'text-accent-yellow-400',
      gradient: { start: '#FBBF24', end: '#F59E0B' },
    },
    red: {
      bg: 'from-accent-red-400 to-accent-red-600',
      glow: 'shadow-glow-red',
      text: 'text-accent-red-400',
      gradient: { start: '#EF4444', end: '#DC2626' },
    },
  };

  const sizeClasses = {
    sm: 'w-24 h-24',
    md: 'w-32 h-32',
    lg: 'w-40 h-40',
  };

  const renderCircularProgress = () => {
    const radius = size === 'sm' ? 40 : size === 'md' ? 56 : 72;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className="relative flex items-center justify-center">
        <svg className={sizeClasses[size]} style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            cx="50%"
            cy="50%"
            r={radius}
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            cx="50%"
            cy="50%"
            r={radius}
            fill="none"
            stroke={`url(#gradient-${color})`}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-out"
          />
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={colorClasses[color].gradient.start} />
              <stop offset="100%" stopColor={colorClasses[color].gradient.end} />
            </linearGradient>
          </defs>
        </svg>
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {icon && <div className="mb-1">{icon}</div>}
          <div className={clsx('font-bold', colorClasses[color].text, size === 'sm' ? 'text-lg' : size === 'md' ? 'text-2xl' : 'text-3xl')}>
            {showPercentage ? `${Math.round(percentage)}%` : `${value}${unit}`}
          </div>
        </div>
      </div>
    );
  };

  const renderLinearProgress = () => (
    <div className="w-full">
      <div className="h-3 bg-dark-bg-tertiary rounded-full overflow-hidden">
        <div
          className={clsx('h-full bg-gradient-to-r transition-all duration-1000 ease-out', colorClasses[color].bg, colorClasses[color].glow)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );

  return (
    <div className={clsx('glass-card p-6 animate-slide-up', colorClasses[color].glow, className)}>
      <div className="flex flex-col items-center">
        {type === 'circular' && renderCircularProgress()}
        {type === 'linear' && renderLinearProgress()}
        
        <div className="mt-4 text-center">
          <div className="text-lg font-semibold text-white">{label}</div>
          {subtitle && (
            <div className="text-sm text-dark-text-secondary mt-1">{subtitle}</div>
          )}
          {type === 'linear' && (
            <div className={clsx('text-2xl font-bold mt-2', colorClasses[color].text)}>
              {value}{unit}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProgressCard;
