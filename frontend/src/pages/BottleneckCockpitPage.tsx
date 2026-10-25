import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  RotateCcw, 
  Search, 
  Clock, 
  Flame, 
  ShieldAlert, 
  ArrowRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface BottleneckItem {
  id: string;
  case_type: string;
  reference_no: string;
  institution_name: string;
  region_name: string;
  current_status: string;
  holding_side: string;
  responsible_party: string;
  age_days: number;
  deadline_days_remaining: number;
  is_overdue: boolean;
  escalation_state: string;
  blocker_reason: string;
  next_permissible_action: string;
}

interface BottleneckSummary {
  total_exceptions: number;
  waiting_on_institution: number;
  waiting_on_aicte: number;
  overdue_count: number;
  critical_escalations: number;
  items: BottleneckItem[];
}

export const BottleneckCockpitPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<BottleneckSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab & Filters
  const [activeTab, setActiveTab] = useState<'ALL' | 'INSTITUTION' | 'AICTE' | 'OVERDUE'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchExceptions = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/bottlenecks/exceptions', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const summary = await res.json();
      setData(summary);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch bottleneck exceptions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptions();
  }, [token]);

  const items = data ? data.items : [];

  const tabFiltered = items.filter((item) => {
    if (activeTab === 'INSTITUTION') return item.holding_side === 'WAITING_ON_INSTITUTION';
    if (activeTab === 'AICTE') return item.holding_side === 'WAITING_ON_AICTE';
    if (activeTab === 'OVERDUE') return item.is_overdue;
    return true;
  });

  const filtered = tabFiltered.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.reference_no.toLowerCase().includes(q) ||
      item.institution_name.toLowerCase().includes(q) ||
      item.blocker_reason.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-amber-600" />
            Bottleneck & Exception Cockpit
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Automated triage isolating stalled cases: Waiting on Institution vs Waiting on AICTE Internal
          </p>
        </div>

        <button
          onClick={fetchExceptions}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded shadow-sm transition-colors"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-teal-600 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Cockpit</span>
        </button>
      </div>

      {/* KPI Cards Row */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-slate-500">Total Exceptions</div>
              <div className="text-2xl font-bold text-slate-900 mt-1">{data.total_exceptions}</div>
            </div>
            <div className="p-2.5 bg-slate-100 text-slate-700 rounded-full">
              <Clock className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-slate-500">Waiting on Institution</div>
              <div className="text-2xl font-bold text-amber-600 mt-1">{data.waiting_on_institution}</div>
              <div className="text-[10px] text-amber-700">Deficiencies & Proofs</div>
            </div>
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-full">
              <Building2 className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-slate-500">Waiting on AICTE Internal</div>
              <div className="text-2xl font-bold text-teal-700 mt-1">{data.waiting_on_aicte}</div>
              <div className="text-[10px] text-teal-700">RO / EVC / SAC / Auth</div>
            </div>
            <div className="p-2.5 bg-teal-50 text-teal-700 rounded-full">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-slate-500">Overdue Breaches</div>
              <div className="text-2xl font-bold text-rose-600 mt-1">{data.overdue_count}</div>
              <div className="text-[10px] text-rose-700">{data.critical_escalations} Critical Escalations</div>
            </div>
            <div className="p-2.5 bg-rose-50 text-rose-600 rounded-full">
              <Flame className="w-5 h-5" />
            </div>
          </div>
        </div>
      )}

      {/* Tabs & Search */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
          <button
            onClick={() => setActiveTab('ALL')}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
              activeTab === 'ALL'
                ? 'bg-navy-800 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            All Exceptions ({data ? data.total_exceptions : 0})
          </button>
          <button
            onClick={() => setActiveTab('INSTITUTION')}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
              activeTab === 'INSTITUTION'
                ? 'bg-amber-600 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Waiting on Institution ({data ? data.waiting_on_institution : 0})
          </button>
          <button
            onClick={() => setActiveTab('AICTE')}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
              activeTab === 'AICTE'
                ? 'bg-teal-700 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Waiting on AICTE ({data ? data.waiting_on_aicte : 0})
          </button>
          <button
            onClick={() => setActiveTab('OVERDUE')}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
              activeTab === 'OVERDUE'
                ? 'bg-rose-700 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Overdue Only ({data ? data.overdue_count : 0})
          </button>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search exceptions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs sm:text-sm border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Exception Records Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            Analyzing stalled regulatory cases...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 bg-rose-50">
            Error: {error}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            No exceptions currently stalled in this category.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <th className="py-3 px-4">Case Reference & Type</th>
                  <th className="py-3 px-4">Holding Responsibility</th>
                  <th className="py-3 px-4">Institution & Region</th>
                  <th className="py-3 px-4">Age / Days Overdue</th>
                  <th className="py-3 px-4">Operational Blocker Rationale</th>
                  <th className="py-3 px-4">Next Permissible Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-mono font-bold text-slate-900">{item.reference_no}</div>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border">
                        {item.case_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${
                        item.holding_side === 'WAITING_ON_INSTITUTION'
                          ? 'bg-amber-100 text-amber-800 border-amber-300'
                          : 'bg-teal-100 text-teal-800 border-teal-300'
                      }`}>
                        {item.holding_side === 'WAITING_ON_INSTITUTION' ? 'Institution Holding' : 'AICTE Internal'}
                      </span>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        {item.responsible_party}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-800">{item.institution_name}</div>
                      <div className="text-[10px] text-slate-500">{item.region_name}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{item.age_days} days in state</div>
                      {item.is_overdue ? (
                        <span className="text-[10px] font-bold text-rose-600">
                          {Math.abs(item.deadline_days_remaining)}d past deadline
                        </span>
                      ) : (
                        <span className="text-[10px] text-slate-500">
                          {item.deadline_days_remaining}d remaining
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 max-w-xs text-slate-700">
                      <p className="line-clamp-2">{item.blocker_reason}</p>
                    </td>
                    <td className="py-3 px-4 text-teal-800 font-medium max-w-xs">
                      <div className="flex items-start gap-1">
                        <ArrowRight className="w-3.5 h-3.5 text-teal-600 shrink-0 mt-0.5" />
                        <span>{item.next_permissible_action}</span>
                      </div>
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
