/**
 * HeroCard Component - Easy·A Style
 * Large gradient card with floating elements and hero content
 */

import React from 'react';
import { clsx } from 'clsx';

interface HeroCardProps {
  title: string;
  subtitle?: string;
  stats?: Array<{
    label: string;
    value: string | number;
    icon?: React.ReactNode;
  }>;
  action?: React.ReactNode;
  gradient?: 'purple-blue' | 'purple-green' | 'purple-pink' | 'dark-purple' | 'lime-green';
  className?: string;
  children?: React.ReactNode;
}

export const HeroCard: React.FC<HeroCardProps> = ({
  title,
  subtitle,
  stats = [],
  action,
  gradient = 'dark-purple',
  className = '',
  children,
}) => {
  const gradientClasses = {
    'purple-blue': 'bg-gradient-purple-blue',
    'purple-green': 'bg-gradient-purple-green',
    'purple-pink': 'bg-gradient-purple-pink',
    'dark-purple': 'bg-gradient-dark-purple',
    'lime-green': 'bg-gradient-lime-green',
  };

  return (
    <div
      className={clsx(
        'relative overflow-hidden rounded-3xl p-8 md:p-12',
        'shadow-glass-lg backdrop-blur-xl',
        'border border-white/10',
        'animate-scale-in',
        gradientClasses[gradient],
        className
      )}
    >
      {/* Floating decorative elements */}
      <div className="absolute top-10 right-10 w-32 h-32 bg-brand-purple-500/20 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-10 left-10 w-40 h-40 bg-accent-green-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }} />
      
      {/* Content */}
      <div className="relative z-10">
        {/* Title Section */}
        <div className="mb-8">
          <h1 className="text-display-lg font-bold text-white mb-3 text-shadow-lg">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xl text-dark-text-secondary">
              {subtitle}
            </p>
          )}
        </div>

        {/* Stats Grid */}
        {stats.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="glass-card p-4 animate-slide-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {stat.icon && (
                  <div className="mb-2 text-brand-purple-400">{stat.icon}</div>
                )}
                <div className="text-display-lg font-bold text-white">
                  {stat.value}
                </div>
                <div className="text-sm text-dark-text-secondary mt-1">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Custom children content */}
        {children}

        {/* Action */}
        {action && (
          <div className="mt-8">
            {action}
          </div>
        )}
      </div>
    </div>
  );
};

export default HeroCard;
