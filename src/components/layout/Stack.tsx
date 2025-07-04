import type { ReactNode } from 'react';

interface StackProps {
  children: ReactNode;
  direction?: 'vertical' | 'horizontal';
  spacing?: 'sm' | 'md' | 'lg' | 'xl';
  align?: 'start' | 'center' | 'end' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around';
  className?: string;
  'data-name'?: string;
}

export function Stack({ 
  children, 
  direction = 'vertical',
  spacing = 'md',
  align = 'stretch',
  justify = 'start',
  className = '',
  'data-name': dataName
}: StackProps) {
  const directionClasses = {
    vertical: 'flex-col',
    horizontal: 'flex-row'
  };

  const spacingClasses = {
    vertical: {
      sm: 'space-y-2',
      md: 'space-y-4',
      lg: 'space-y-6',
      xl: 'space-y-8'
    },
    horizontal: {
      sm: 'space-x-2',
      md: 'space-x-4',
      lg: 'space-x-6',
      xl: 'space-x-8'
    }
  };

  const alignClasses = {
    start: 'items-start',
    center: 'items-center',
    end: 'items-end',
    stretch: 'items-stretch'
  };

  const justifyClasses = {
    start: 'justify-start',
    center: 'justify-center',
    end: 'justify-end',
    between: 'justify-between',
    around: 'justify-around'
  };

  return (
    <div className={`flex ${directionClasses[direction]} ${spacingClasses[direction][spacing]} ${alignClasses[align]} ${justifyClasses[justify]} ${className}`} data-name={dataName}>
      {children}
    </div>
  );
}