import type { ReactNode } from 'react';

interface HeaderSectionProps {
  children: ReactNode;
  'data-name'?: string;
}

export function HeaderSection({ children, 'data-name': dataName }: HeaderSectionProps) {
  return (
    <div className="bg-white shadow-sm border-b" data-name={dataName}>
      <div className="w-[1280px] mx-auto px-4 py-6">
        {children}
      </div>
    </div>
  );
}