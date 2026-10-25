import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Search, 
  Filter, 
  Building2, 
  RotateCcw, 
  HelpCircle, 
  Sparkles
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface AttentionFactor {
  factor_name: string;
  weight: number;
  points_awarded: number;
  rationale: string;
}

interface AttentionQueueItem {
  application_id: string;
  application_no: string;
  institution_name: string;
  region_name: string;
  current_stage: string;
  priority_level: string;
  composite_score: number;
  days_in_stage: number;
  days_to_deadline: number;
  is_overdue: boolean;
  responsible_role: string;
  assigned_officer: string | null;
  blocking_dependency: string;
  recommended_action: string;
  explanation: string;
  factors: AttentionFactor[];
}

interface CaseSummary {
  application_no: string;
  institution_name: string;
  route: string;
  current_stage: string;
  status: string;
  questions: {
    q1_what_needs_attention: string;
    q2_why_pending: string;
    q3_who_responsible: string;
    q4_what_happens_next: string;
    q5_can_be_traced: string;
  };
}

export const AttentionQueuePage: React.FC = () => {
  const { token } = useAuth();
  const [queue, setQueue] = useState<AttentionQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [tierFilter, setTierFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Case Summary Modal
  const [summaryModal, setSummaryModal] = useState<{ open: boolean; data: CaseSummary | null; loading: boolean }>({
    open: false,
    data: null,
    loading: false
  });

  const fetchQueue = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/attention/queue', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setQueue(data);
    } catch (err: any) {
      setError(err.message || 'Failed to compute attention queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [token]);

  const openSummary = async (appId: string) => {
    if (!token) return;
    setSummaryModal({ open: true, data: null, loading: true });
    try {
      const res = await fetch(`/api/attention/applications/${appId}/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSummaryModal({ open: true, data, loading: false });
    } catch (err: any) {
      alert(`Summary error: ${err.message}`);
      setSummaryModal({ open: false, data: null, loading: false });
    }
  };

  const filtered = queue.filter((item) => {
    if (tierFilter && item.priority_level !== tierFilter) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.application_no.toLowerCase().includes(q) ||
      item.institution_name.toLowerCase().includes(q) ||
      item.responsible_role.toLowerCase().includes(q) ||
      item.explanation.toLowerCase().includes(q)
    );
  });

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'CRITICAL':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'MEDIUM':
        return 'bg-teal-100 text-teal-800 border-teal-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300';
    }
  };

  const criticalCount = queue.filter((i) => i.priority_level === 'CRITICAL').length;
  const highCount = queue.filter((i) => i.priority_level === 'HIGH').length;

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-teal-600 text-white rounded shadow-sm">
              <Zap className="w-4 h-4 fill-current" />
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Explainable Attention Engine (Priority Queue)
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Deterministic multi-factor scoring replacing arbitrary queues with transparent operational intelligence
          </p>
        </div>

        <button
          onClick={fetchQueue}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded shadow-sm transition-colors"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-teal-600 ${loading ? 'animate-spin' : ''}`} />
          <span>Recalculate Priorities</span>
        </button>
      </div>

      {/* Rationale Banner */}
      <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg text-xs space-y-1.5 text-teal-950">
        <div className="font-bold flex items-center gap-1.5 text-teal-900">
          <Sparkles className="w-4 h-4 text-teal-700" />
          Multi-Factor Objective Urgency Algorithm
        </div>
        <p className="text-[11px] text-teal-800 leading-relaxed">
          The engine computes composite priority scores (0 to 100) combining 6 weighted regulatory factors:
          <strong> SLA deadline proximity & breaches</strong> (40%), <strong>chronic deficiency returns</strong> (20%), 
          <strong> missing/overdue compliance undertakings</strong> (20%), <strong>unverified or expired lease deeds</strong> (15%), 
          <strong> stalled EVC visits</strong> (15%), and <strong>unassigned case officers</strong> (10%).
        </p>
        <div className="flex gap-4 pt-1 font-mono text-[11px]">
          <div>Total Cases Evaluated: <strong>{queue.length}</strong></div>
          <div>Critical Priority: <strong className="text-rose-700">{criticalCount}</strong></div>
          <div>High Priority: <strong className="text-amber-700">{highCount}</strong></div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by application, institution, or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs sm:text-sm border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Priority Tiers</option>
            <option value="CRITICAL">Critical (&ge; 70 pts)</option>
            <option value="HIGH">High (&ge; 45 pts)</option>
            <option value="MEDIUM">Medium (&ge; 25 pts)</option>
            <option value="LOW">Low (&lt; 25 pts)</option>
          </select>
        </div>
      </div>

      {/* Priority Queue Cards */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border">
          Evaluating multi-factor priority equations...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 rounded-lg border border-rose-200">
          Error: {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border">
          No cases match your priority query.
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((item, idx) => (
            <div
              key={item.application_id}
              className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3.5 hover:border-teal-400 transition-colors"
            >
              {/* Card Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center font-bold text-xs text-slate-600">
                    #{idx + 1}
                  </div>
                  <div>
                    <span className="font-mono font-bold text-slate-900 text-sm">{item.application_no}</span>
                    <span className="text-xs text-slate-500 ml-2">({item.current_stage})</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-0.5 rounded text-xs font-bold border ${getTierBadge(item.priority_level)}`}>
                    {item.priority_level} ({item.composite_score}/100)
                  </span>

                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border">
                    Role: {item.responsible_role}
                  </span>
                </div>
              </div>

              {/* Institution and Age */}
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-600">
                <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-teal-700" />
                  {item.institution_name} ({item.region_name})
                </div>

                <div className="flex items-center gap-3">
                  <span>In Stage: <strong>{item.days_in_stage}d</strong></span>
                  <span className={item.is_overdue ? 'text-rose-600 font-bold' : 'text-slate-600'}>
                    {item.is_overdue ? `${Math.abs(item.days_to_deadline)}d Overdue` : `${item.days_to_deadline}d to SLA`}
                  </span>
                </div>
              </div>

              {/* Plain-English Explanation */}
              <div className="p-3 bg-slate-50 rounded border text-xs text-slate-700 space-y-1">
                <div className="font-bold text-slate-800 text-[11px] uppercase tracking-wider">
                  Operational Urgency Diagnostic:
                </div>
                <p className="leading-relaxed">{item.explanation}</p>

                {/* Factors Chips */}
                <div className="flex flex-wrap gap-1.5 pt-1.5">
                  {item.factors.map((f, fIdx) => (
                    <span
                      key={fIdx}
                      title={f.rationale}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-white border border-slate-200 text-slate-700 shadow-2xs"
                    >
                      <span className="font-bold text-teal-700">+{f.points_awarded}</span>
                      <span>{f.factor_name.replace(/_/g, ' ')}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Prescriptive Recommended Next Step */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                <div className="text-xs text-teal-900 font-medium">
                  <strong>Prescriptive Next Step:</strong> {item.recommended_action}
                </div>

                <button
                  onClick={() => openSummary(item.application_id)}
                  className="shrink-0 inline-flex items-center gap-1 px-3 py-1 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-300 rounded shadow-sm transition-colors"
                >
                  <HelpCircle className="w-3.5 h-3.5" /> 5-Question Case Summary
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Case Summary Modal */}
      {summaryModal.open && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-5 space-y-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-base border-b pb-2 flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-teal-700" />
              Structured 5-Question Operational Summary
            </h3>

            {summaryModal.loading ? (
              <div className="p-8 text-center text-xs text-slate-500">
                Synthesizing immutable case history...
              </div>
            ) : summaryModal.data ? (
              <div className="space-y-3 text-xs">
                <div className="bg-slate-50 p-2.5 rounded border text-[11px] font-mono">
                  Application: <strong>{summaryModal.data.application_no}</strong> ({summaryModal.data.route}) | 
                  Institution: <strong>{summaryModal.data.institution_name}</strong>
                </div>

                <div className="space-y-2.5">
                  <div className="p-2.5 bg-teal-50/50 border border-teal-200/70 rounded">
                    <div className="font-bold text-teal-900">1. Which obligation or application needs attention?</div>
                    <div className="text-slate-700 mt-0.5">{summaryModal.data.questions.q1_what_needs_attention}</div>
                  </div>

                  <div className="p-2.5 bg-amber-50/50 border border-amber-200/70 rounded">
                    <div className="font-bold text-amber-900">2. Why is it pending or at risk of becoming overdue?</div>
                    <div className="text-slate-700 mt-0.5">{summaryModal.data.questions.q2_why_pending}</div>
                  </div>

                  <div className="p-2.5 bg-purple-50/50 border border-purple-200/70 rounded">
                    <div className="font-bold text-purple-900">3. Who is responsible for the next action?</div>
                    <div className="text-slate-700 mt-0.5">{summaryModal.data.questions.q3_who_responsible}</div>
                  </div>

                  <div className="p-2.5 bg-blue-50/50 border border-blue-200/70 rounded">
                    <div className="font-bold text-blue-900">4. What must happen next, and by when?</div>
                    <div className="text-slate-700 mt-0.5">{summaryModal.data.questions.q4_what_happens_next}</div>
                  </div>

                  <div className="p-2.5 bg-emerald-50/50 border border-emerald-200/70 rounded">
                    <div className="font-bold text-emerald-900">5. Can every significant action be traced?</div>
                    <div className="text-slate-700 mt-0.5">{summaryModal.data.questions.q5_can_be_traced}</div>
                  </div>
                </div>
              </div>
            ) : null}

            <div className="flex justify-end pt-2 border-t">
              <button
                onClick={() => setSummaryModal({ open: false, data: null, loading: false })}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded border border-slate-300"
              >
                Close Summary
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
