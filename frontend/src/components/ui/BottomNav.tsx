/**
 * BottomNav Component - Mobile Navigation
 * Glassmorphism bottom navigation bar
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  activeIcon?: React.ReactNode;
}

interface BottomNavProps {
  items: NavItem[];
  className?: string;
}

export const BottomNav: React.FC<BottomNavProps> = ({ items, className = '' }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <nav
      className={clsx(
        'fixed bottom-0 left-0 right-0 z-50',
        'glass-card border-t border-white/10',
        'px-4 py-2',
        'md:hidden', // Only show on mobile
        className
      )}
      style={{
        backdropFilter: 'blur(20px)',
        paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))',
      }}
    >
      <div className="flex justify-around items-center max-w-lg mx-auto">
        {items.map((item) => {
          const active = isActive(item.path);
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={clsx(
                'flex flex-col items-center justify-center',
                'px-4 py-2 rounded-xl',
                'transition-all duration-300',
                'min-w-[60px]',
                active
                  ? 'text-brand-purple-400 scale-110'
                  : 'text-dark-text-secondary hover:text-white'
              )}
            >
              <div
                className={clsx(
                  'text-2xl mb-1 transition-all duration-300',
                  active && 'animate-bounce-slow'
                )}
              >
                {active && item.activeIcon ? item.activeIcon : item.icon}
              </div>
              <span
                className={clsx(
                  'text-xs font-medium transition-all duration-300',
                  active && 'font-semibold'
                )}
              >
                {item.label}
              </span>
              {active && (
                <div className="absolute -bottom-1 w-1 h-1 bg-brand-purple-400 rounded-full shadow-glow-purple" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default BottomNav;
