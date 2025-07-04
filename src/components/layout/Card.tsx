import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  shadow?: 'sm' | 'md' | 'lg' | 'none';
  'data-name'?: string;
}

export function Card({ 
  children, 
  className = '', 
  padding = 'md',
  shadow = 'md',
  'data-name': dataName
}: CardProps) {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6', 
    lg: 'p-8'
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg'
  };

  return (
    <div className={`bg-white rounded-lg ${shadowClasses[shadow]} ${paddingClasses[padding]} ${className}`} data-name={dataName}>
      {children}
    </div>
  );
}