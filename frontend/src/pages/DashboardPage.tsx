import React, { useEffect, useState } from 'react';
import { 
  Activity, 
  Database, 
  Server, 
  FileCheck2, 
  Clock, 
  AlertCircle,
  ExternalLink,
  RefreshCw
} from 'lucide-react';

interface HealthData {
  status: string;
  version: string;
  environment: string;
  database_connected: boolean;
  details: {
    storage_writable: boolean;
    demo_mode: boolean;
    timezone: string;
  };
}

export const DashboardPage: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/health');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to SETU backend API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title & Top Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            AICTE Operations Dashboard
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Real-time workflow monitoring, pendency tracking, and regulatory intelligence
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchHealth}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded shadow-sm hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Backend & DB System Verification Card */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-teal-600" />
            <h3 className="font-semibold text-sm sm:text-base text-slate-800">
              System Verification & Runtime Status (Milestone 1)
            </h3>
          </div>
          <span className="text-xs font-mono bg-teal-50 text-teal-700 px-2.5 py-1 rounded-full border border-teal-200">
            SIH26262 Prototype
          </span>
        </div>

        {loading ? (
          <div className="text-xs text-slate-500 py-4 flex items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-teal-600" />
            Probing backend health & database connectivity...
          </div>
        ) : error ? (
          <div className="bg-rose-50 border border-rose-200 rounded p-3 text-xs text-rose-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>Connection check failed: {error} (Ensure backend server is running on port 8000)</span>
          </div>
        ) : health ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-50 p-3 rounded border border-slate-200">
              <div className="text-slate-500 mb-1 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-teal-600" />
                API Service Status
              </div>
              <div className="font-semibold text-slate-900 text-sm capitalize flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                {health.status} (v{health.version})
              </div>
            </div>

            <div className="bg-slate-50 p-3 rounded border border-slate-200">
              <div className="text-slate-500 mb-1 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-teal-600" />
                Database Engine
              </div>
              <div className="font-semibold text-slate-900 text-sm flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${health.database_connected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
                {health.database_connected ? 'Connected & Migrated' : 'Disconnected'}
              </div>
            </div>

            <div className="bg-slate-50 p-3 rounded border border-slate-200">
              <div className="text-slate-500 mb-1 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-teal-600" />
                Timezone Context
              </div>
              <div className="font-semibold text-slate-900 text-sm font-mono">
                {health.details.timezone || 'Asia/Kolkata'}
              </div>
            </div>

            <div className="bg-slate-50 p-3 rounded border border-slate-200">
              <div className="text-slate-500 mb-1 flex items-center gap-1.5">
                <FileCheck2 className="w-3.5 h-3.5 text-teal-600" />
                Local Storage Writable
              </div>
              <div className="font-semibold text-slate-900 text-sm flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                {health.details.storage_writable ? 'Verified (SHA-256)' : 'Storage error'}
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Operational KPI Grid Preview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
            Active Applications
          </div>
          <div className="text-2xl font-bold text-slate-900">28</div>
          <div className="text-[11px] text-teal-600 font-medium mt-1">Across 4 Workflow Routes</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
            Pending Scrutiny
          </div>
          <div className="text-2xl font-bold text-amber-600">9</div>
          <div className="text-[11px] text-slate-500 mt-1">SLA target: &le; 14 days</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
            EVC Inspections
          </div>
          <div className="text-2xl font-bold text-blue-600">6</div>
          <div className="text-[11px] text-blue-700 mt-1">4 scheduled &bull; 2 awaiting</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
            Critical Alerts
          </div>
          <div className="text-2xl font-bold text-rose-600">3</div>
          <div className="text-[11px] text-rose-700 mt-1">2 Overdue &bull; 1 Doc Expiry</div>
        </div>
      </div>

      {/* Core Innovation Direct Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white p-5 rounded-lg border border-slate-700 shadow">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider bg-teal-500 text-slate-950 font-bold px-2 py-0.5 rounded">
              P1 Innovation A
            </span>
          </div>
          <h3 className="font-bold text-base mb-1">Explainable Attention Engine</h3>
          <p className="text-xs text-slate-300 mb-4">
            Transparent, multi-factor deterministic scoring prioritizing cases that require immediate official action without automated statutory decision-making.
          </p>
          <a
            href="/attention"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-teal-400 hover:text-teal-300"
          >
            Launch Attention Queue <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white p-5 rounded-lg border border-slate-700 shadow">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider bg-amber-400 text-slate-950 font-bold px-2 py-0.5 rounded">
              P1 Innovation C
            </span>
          </div>
          <h3 className="font-bold text-base mb-1">Bottleneck & Exception Cockpit</h3>
          <p className="text-xs text-slate-300 mb-4">
            Isolates stuck cases, explicitly separating delays caused by institutions (clarifications, deficient evidence) from internal AICTE administrative queues.
          </p>
          <a
            href="/bottlenecks"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-400 hover:text-amber-300"
          >
            Launch Bottleneck Cockpit <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
};
