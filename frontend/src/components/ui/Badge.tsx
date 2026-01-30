/**
 * TB Personal OS - Badge Component (Unified)
 */

import React from 'react';
import { clsx } from 'clsx';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'green' | 'blue' | 'pink';
  size?: 'sm' | 'md' | 'lg';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className,
  ...props
}) => {
  const variants: Record<string, string> = {
    default: 'bg-gray-100 text-gray-800 dark:bg-dark-bg-tertiary dark:text-dark-text-secondary',
    primary: 'bg-blue-100 text-blue-800 dark:bg-brand-blue-500/20 dark:text-brand-blue-300 dark:border dark:border-brand-blue-500/30',
    success: 'bg-green-100 text-green-800 dark:bg-accent-green/20 dark:text-accent-green dark:border dark:border-accent-green/30',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800 dark:bg-accent-pink/20 dark:text-accent-pink dark:border dark:border-accent-pink/30',
    info: 'bg-cyan-100 text-cyan-800 dark:bg-brand-blue-500/20 dark:text-brand-blue-300 dark:border dark:border-brand-blue-500/30',
    purple: 'badge-purple',
    green: 'badge-green',
    blue: 'bg-brand-blue-500/20 text-brand-blue-300 border border-brand-blue-500/30',
    pink: 'bg-accent-pink/20 text-accent-pink border border-accent-pink/30',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export default Badge;
