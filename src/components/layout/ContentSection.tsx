import type { ReactNode } from 'react';

interface ContentSectionProps {
  children: ReactNode;
  className?: string;
  'data-name'?: string;
}

export function ContentSection({ children, className = '', 'data-name': dataName }: ContentSectionProps) {
  return (
    <div className={`max-w-7xl mx-auto px-4 py-6 ${className}`} data-name={dataName}>
      {children}
    </div>
  );
}