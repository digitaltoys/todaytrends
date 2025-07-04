import type { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
  'data-name'?: string;
}

export function Layout({ children, 'data-name': dataName }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50" data-name={dataName}>
      {children}
    </div>
  );
}