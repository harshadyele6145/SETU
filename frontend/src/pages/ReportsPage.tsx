import React, { useState, useEffect } from 'react';
import { 
  Download, 
  Search, 
  Filter, 
  RotateCcw, 
  Clock, 
  AlertTriangle, 
  Building2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface PendencyRow {
  id: string;
  application_no: string;
  institution_name: string;
  region_name: string;
  route: string;
  status: string;
  current_stage: string;
  sla_limit_days: number;
  stage_age_days: number;
  total_age_days: number;
  is_overdue: boolean;
  holding_party: string;
  return_count: number;
}

export const ReportsPage: React.FC = () => {
  const { token } = useAuth();
  const [rows, setRows] = useState<PendencyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [routeFilter, setRouteFilter] = useState('');
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [exporting, setExporting] = useState(false);

  const fetchPendency = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      let url = '/api/reports/pendency?';
      if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}&`;
      if (routeFilter) url += `route=${encodeURIComponent(routeFilter)}&`;
      if (overdueOnly) url += `overdue_only=true&`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRows(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch pendency reports');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendency();
  }, [token, statusFilter, routeFilter, overdueOnly]);

  const handleExportCSV = async () => {
    if (!token) return;
    setExporting(true);
    try {
      let url = '/api/reports/export?';
      if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}&`;
      if (routeFilter) url += `route=${encodeURIComponent(routeFilter)}&`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `setu_pendency_report_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const filtered = rows.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.application_no.toLowerCase().includes(q) ||
      r.institution_name.toLowerCase().includes(q) ||
      r.current_stage.toLowerCase().includes(q)
    );
  });

  const overdueCount = rows.filter((r) => r.is_overdue).length;
  const instHoldingCount = rows.filter((r) => r.holding_party === 'INSTITUTION').length;
  const aicteHoldingCount = rows.filter((r) => r.holding_party === 'AICTE_INTERNAL').length;

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Pendency & Regulatory SLA Analytics
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Granular stage aging, holding responsibility breakdown, and authorized CSV report exports
          </p>
        </div>

        <button
          onClick={handleExportCSV}
          disabled={exporting || rows.length === 0}
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white text-xs sm:text-sm font-semibold rounded shadow transition-colors disabled:opacity-50"
        >
          {exporting ? (
            <RotateCcw className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          <span>{exporting ? 'Generating CSV...' : 'Export Scoped CSV'}</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Overdue SLA Breaches</div>
            <div className="text-2xl font-bold text-rose-600">{overdueCount}</div>
          </div>
          <div className="p-2.5 bg-rose-50 text-rose-600 rounded-full">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Waiting on Institution</div>
            <div className="text-2xl font-bold text-amber-600">{instHoldingCount}</div>
          </div>
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-full">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Waiting on AICTE Internal</div>
            <div className="text-2xl font-bold text-teal-700">{aicteHoldingCount}</div>
          </div>
          <div className="p-2.5 bg-teal-50 text-teal-700 rounded-full">
            <Building2 className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by application or institution..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs sm:text-sm border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={routeFilter}
            onChange={(e) => setRouteFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Routes</option>
            <option value="ROUTE_A">Route A (New Campus)</option>
            <option value="ROUTE_B">Route B (Autonomous/EoA)</option>
            <option value="ROUTE_C">Route C (Expansion/NRI)</option>
            <option value="ROUTE_D">Route D (Special/Change)</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Stages</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="UNDER_SCRUTINY">Under Scrutiny</option>
            <option value="PENDING_CLARIFICATION">Pending Clarification</option>
            <option value="EVC_SCHEDULED">EVC Scheduled</option>
            <option value="SAC_RECOMMENDED">SAC Recommended</option>
          </select>

          <label className="flex items-center gap-1.5 text-xs cursor-pointer select-none text-rose-700 font-semibold">
            <input
              type="checkbox"
              checked={overdueOnly}
              onChange={(e) => setOverdueOnly(e.target.checked)}
              className="rounded text-rose-600 focus:ring-rose-500"
            />
            <span>Overdue Breaches Only</span>
          </label>
        </div>
      </div>

      {/* Pendency Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            Calculating granular pendency analytics...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 bg-rose-50">
            Error: {error}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            No application records match your filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <th className="py-3 px-4">Application No & Route</th>
                  <th className="py-3 px-4">Institution & Region</th>
                  <th className="py-3 px-4">Current Stage & Status</th>
                  <th className="py-3 px-4">Stage Age / SLA Limit</th>
                  <th className="py-3 px-4">Total Age</th>
                  <th className="py-3 px-4">Holding Responsibility</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-teal-800">
                      <div>{r.application_no}</div>
                      <div className="text-[10px] text-slate-500 font-sans">{r.route}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-800">{r.institution_name}</div>
                      <div className="text-[10px] text-slate-500">{r.region_name}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-900">{r.current_stage}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{r.status}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <span className={`font-bold ${r.is_overdue ? 'text-rose-600' : 'text-slate-800'}`}>
                          {r.stage_age_days}d
                        </span>
                        <span className="text-slate-400">/ SLA: {r.sla_limit_days}d</span>
                      </div>
                      {r.is_overdue && (
                        <div className="text-[10px] text-rose-600 font-semibold">
                          Overdue by {r.stage_age_days - r.sla_limit_days} days
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-medium">
                      {r.total_age_days} days
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        r.holding_party === 'INSTITUTION' 
                          ? 'bg-amber-100 text-amber-800 border-amber-300' 
                          : 'bg-teal-100 text-teal-800 border-teal-300'
                      }`}>
                        {r.holding_party === 'INSTITUTION' ? 'Institution' : 'AICTE Internal'}
                      </span>
                      {r.return_count > 0 && (
                        <div className="text-[10px] text-slate-500 mt-0.5">
                          Returns: {r.return_count}x
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
