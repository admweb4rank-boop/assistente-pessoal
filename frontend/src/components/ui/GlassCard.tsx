import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export const GlassCard: React.FC<GlassCardProps> = ({ 
  children, 
  className = '', 
  hover = false,
  onClick,
  style 
}) => {
  const baseClass = hover ? 'glass-card-hover' : 'glass-card';
  
  return (
    <div 
      className={`${baseClass} ${className} ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
      style={style}
    >
      {children}
    </div>
  );
};
