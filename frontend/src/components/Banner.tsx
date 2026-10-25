import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const DemoBanner: React.FC = () => {
  return (
    <div 
      role="banner"
      className="bg-amber-500 text-slate-950 font-semibold px-4 py-1.5 text-xs sm:text-sm flex items-center justify-center gap-2 shadow-inner border-b border-amber-600 tracking-wide select-none"
    >
      <AlertTriangle className="w-4 h-4 text-slate-950 shrink-0" aria-hidden="true" />
      <span>DEMO ENVIRONMENT — FICTIONAL DATA — NOT CONNECTED TO AICTE SYSTEMS</span>
    </div>
  );
};
