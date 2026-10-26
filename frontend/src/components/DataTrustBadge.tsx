import React from 'react';
import { Database, ShieldCheck, Sparkles } from 'lucide-react';

interface DataTrustBadgeProps {
  sourceSystem?: string;
  isSynthetic?: boolean;
  compact?: boolean;
}

export const DataTrustBadge: React.FC<DataTrustBadgeProps> = ({
  sourceSystem = 'SETU_OPERATIONAL',
  isSynthetic = false,
  compact = false
}) => {
  if (isSynthetic || sourceSystem === 'SYNTHETIC_SEED') {
    return (
      <span
        className={`inline-flex items-center gap-1 font-mono font-medium rounded border ${
          compact ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5'
        } bg-amber-50 text-amber-800 border-amber-300`}
        title="Category A: Synthetic Seed Data (Fictional record generated for prototype demonstration and load benchmarking)"
      >
        <Sparkles className={compact ? 'w-2.5 h-2.5 text-amber-600' : 'w-3 h-3 text-amber-600'} />
        <span>SYNTHETIC</span>
      </span>
    );
  }

  if (sourceSystem === 'AICTE_ONOD_PUBLIC') {
    return (
      <span
        className={`inline-flex items-center gap-1 font-mono font-medium rounded border ${
          compact ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5'
        } bg-blue-50 text-blue-800 border-blue-300`}
        title="Category B: Public Reference Data (Ingested from official AICTE Open Data Portal / ONOD)"
      >
        <Database className={compact ? 'w-2.5 h-2.5 text-blue-600' : 'w-3 h-3 text-blue-600'} />
        <span>PUBLIC DATA</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1 font-mono font-medium rounded border ${
        compact ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5'
      } bg-emerald-50 text-emerald-800 border-emerald-300`}
      title="Category C: Operational Data (Direct verified institutional submission via SETU platform)"
    >
      <ShieldCheck className={compact ? 'w-2.5 h-2.5 text-emerald-600' : 'w-3 h-3 text-emerald-600'} />
      <span>OPERATIONAL</span>
    </span>
  );
};

