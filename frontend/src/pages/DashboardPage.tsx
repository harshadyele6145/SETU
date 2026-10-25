import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  Clock, 
  Building2, 
  RotateCcw,
  ShieldCheck,
  Flame,
  FileCheck,
  TrendingUp
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  CartesianGrid, 
  Legend 
} from 'recharts';
import { useAuth } from '../context/AuthContext';

interface DashboardStats {
  summary: {
    total_applications: number;
    active_applications: number;
    approved_applications: number;
    rejected_applications: number;
    clarification_pending: number;
    critical_alerts: number;
    unacknowledged_alerts: number;
    escalated_alerts: number;
    overdue_obligations: number;
    expired_documents: number;
  };
  route_distribution: { route: string; count: number }[];
  stage_breakdown: { [key: string]: number };
  regional_workload: {
    region_id: string;
    region_code: string;
    region_name: string;
    total_applications: number;
    active_applications: number;
    overdue_alerts: number;
  }[];
  compliance_health: {
    total: number;
    overdue: number;
    due_soon: number;
    submitted: number;
    verified: number;
  };
  document_health: {
    total: number;
    expiring_soon: number;
    expired: number;
    renewal_submitted: number;
  };
}

const ROUTE_COLORS = ['#0f766e', '#0284c7', '#8b5cf6', '#f59e0b'];

export const DashboardPage: React.FC = () => {
  const { token } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/dashboard/stats', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setStats(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch live dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [token]);

  // Stage funnel data formatting
  const stageData = stats ? [
    { stage: 'Draft', count: stats.stage_breakdown['DRAFT'] || 0 },
    { stage: 'Submitted', count: stats.stage_breakdown['SUBMITTED'] || 0 },
    { stage: 'Scrutiny', count: stats.stage_breakdown['SCRUTINY'] || 0 },
    { stage: 'EVC Visit', count: stats.stage_breakdown['EVC'] || 0 },
    { stage: 'SAC / SHC', count: stats.stage_breakdown['SAC_SHC'] || 0 },
    { stage: 'Final Decision', count: stats.stage_breakdown['DECISION'] || 0 }
  ] : [];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            AICTE Operations Dashboard (Live Metrics)
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Real-time pendency tracking, stage progression, regional workload, and compliance health
          </p>
        </div>

        <button
          onClick={fetchStats}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded shadow-sm transition-colors"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-teal-600 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {loading && !stats ? (
        <div className="p-16 text-center text-xs text-slate-500 bg-white rounded-lg border">
          Computing live regulatory indicators from database...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 rounded-lg border border-rose-200">
          Error: {error}
        </div>
      ) : stats ? (
        <>
          {/* KPI Cards Row */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Total Applications</span>
                <FileText className="w-4 h-4 text-teal-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-2">{stats.summary.total_applications}</div>
              <div className="text-[11px] text-teal-700 font-medium mt-1">
                {stats.summary.active_applications} In Active Progress
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Critical Breaches</span>
                <Flame className="w-4 h-4 text-rose-600" />
              </div>
              <div className="text-2xl font-bold text-rose-600 mt-2">{stats.summary.critical_alerts}</div>
              <div className="text-[11px] text-rose-700 font-medium mt-1">
                {stats.summary.escalated_alerts} Escalated to HQ/RO
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Clarifications</span>
                <Clock className="w-4 h-4 text-amber-600" />
              </div>
              <div className="text-2xl font-bold text-amber-600 mt-2">{stats.summary.clarification_pending}</div>
              <div className="text-[11px] text-amber-700 font-medium mt-1">
                Waiting on Institution
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Compliance Health</span>
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-bold text-emerald-600 mt-2">
                {stats.compliance_health.verified} / {stats.compliance_health.total}
              </div>
              <div className="text-[11px] text-rose-600 font-medium mt-1">
                {stats.compliance_health.overdue} Overdue Undertakings
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Document Expiries</span>
                <FileCheck className="w-4 h-4 text-purple-600" />
              </div>
              <div className="text-2xl font-bold text-purple-700 mt-2">
                {stats.document_health.expiring_soon}
              </div>
              <div className="text-[11px] text-purple-700 font-medium mt-1">
                {stats.document_health.expired} Expired Deeds/NOCs
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Stage Progression Bar Chart */}
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-teal-600" /> Stage Pipeline Distribution
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">Real-time DB query</span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stageData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="stage" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0f766e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Approval Routes Pie Chart */}
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-teal-600" /> Route Distribution (A, B, C, D)
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">APH Routing</span>
              </div>
              <div className="h-64 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stats.route_distribution}
                      dataKey="count"
                      nameKey="route"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {stats.route_distribution.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={ROUTE_COLORS[index % ROUTE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Regional Workload Table & Bar */}
          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b pb-2">
              <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                <Building2 className="w-4 h-4 text-teal-700" /> Regional Workload & Overdue Allocation
              </h3>
              <span className="text-[11px] text-slate-400">5 Geographic AICTE Regions</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                    <th className="py-2.5 px-4">Region Code & Office</th>
                    <th className="py-2.5 px-4">Total Applications</th>
                    <th className="py-2.5 px-4">Active In-Flight</th>
                    <th className="py-2.5 px-4">Overdue Alerts</th>
                    <th className="py-2.5 px-4">Workload Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {stats.regional_workload.map((reg) => (
                    <tr key={reg.region_id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2.5 px-4">
                        <div className="font-bold text-slate-900">{reg.region_name}</div>
                        <div className="text-[10px] font-mono text-teal-700">{reg.region_code}</div>
                      </td>
                      <td className="py-2.5 px-4 font-semibold text-slate-800">{reg.total_applications}</td>
                      <td className="py-2.5 px-4 font-medium text-blue-700">{reg.active_applications}</td>
                      <td className="py-2.5 px-4">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          reg.overdue_alerts > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
                        }`}>
                          {reg.overdue_alerts} Overdue
                        </span>
                      </td>
                      <td className="py-2.5 px-4">
                        <div className="w-full bg-slate-100 rounded-full h-2 max-w-[120px]">
                          <div
                            className="bg-teal-600 h-2 rounded-full"
                            style={{ width: `${Math.min(100, (reg.active_applications / Math.max(1, stats.summary.total_applications)) * 100 * 3)}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
