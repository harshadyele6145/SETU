import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { 
  GitCommit, 
  ArrowLeft, 
  User,
  ShieldCheck,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Lock,
  ArrowRight,
  AlertCircle,
  Activity
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { DataTrustBadge } from '../components/DataTrustBadge';

interface HistoryItem {
  id: string;
  action: string;
  actor_name: string;
  actor_role: string;
  from_stage: string | null;
  to_stage: string | null;
  comments: string | null;
  created_at: string;
}

interface ApplicationDetail {
  id: string;
  application_no: string;
  institution_name: string;
  region_name: string;
  academic_year: string;
  application_type: string;
  route: string;
  status: string;
  current_stage_name: string;
  days_in_stage: number;
  total_days: number;
  source_system?: string;
  is_synthetic?: boolean;
  history: HistoryItem[];
}

interface PermittedActionItem {
  action_key: string;
  action_label: string;
  target_stage_key: string | null;
  endpoint: string;
  http_method: string;
  allowed_roles: string[];
  is_permitted_for_user: boolean;
  description: string;
}

interface AccountabilityBlockerItem {
  type: string;
  title: string;
  status: string;
  detail: string;
  severity: string;
}

interface ApplicationAccountability {
  application_id: string;
  application_no: string;
  institution_name: string;
  institution_aicte_id: string | null;
  region_name: string;
  route: string;
  status: string;
  current_stage_name: string;
  stage_entered_at: string;
  days_in_stage: number;
  sla_limit_days: number;
  deadline: string | null;
  days_remaining: number;
  is_overdue: boolean;
  holding_party: string;
  holding_party_label: string;
  holding_responsible_role: string;
  assigned_officer_name: string | null;
  return_count: number;
  source_system?: string;
  is_synthetic?: boolean;
  current_user_role: string;
  current_user_can_act: boolean;
  permitted_next_actions: PermittedActionItem[];
  attention_score: number;
  attention_tier: string;
  attention_factors: string[];
  blockers: AccountabilityBlockerItem[];
  audit_event_count: number;
  latest_audit_hash: string | null;
}

export const TimelinePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const appIdParam = searchParams.get('app_id');
  const { user, token } = useAuth();

  const [applications, setApplications] = useState<any[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string>(appIdParam || '');
  const [appDetail, setAppDetail] = useState<ApplicationDetail | null>(null);
  const [accountability, setAccountability] = useState<ApplicationAccountability | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Workflow execution modal state
  const [activeAction, setActiveAction] = useState<PermittedActionItem | null>(null);
  const [actionComments, setActionComments] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  // Fetch list of applications for selector
  useEffect(() => {
    if (!token) return;
    fetch('/api/applications', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setApplications(data);
          if (!selectedAppId && data.length > 0) {
            setSelectedAppId(data[0].id);
          }
        }
      })
      .catch(() => {});
  }, [token]);

  // Fetch detail and accountability for selected application
  const fetchCaseData = async (appId: string) => {
    if (!appId || !token) return;
    setLoading(true);
    setError(null);

    try {
      const [detailRes, accRes] = await Promise.all([
        fetch(`/api/applications/${appId}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`/api/applications/${appId}/accountability`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (!detailRes.ok) {
        throw new Error(`Failed to load case detail (HTTP ${detailRes.status})`);
      }

      const detailData = await detailRes.json();
      setAppDetail(detailData);

      if (accRes.ok) {
        const accData = await accRes.json();
        setAccountability(accData);
      } else {
        setAccountability(null);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedAppId) {
      fetchCaseData(selectedAppId);
    }
  }, [selectedAppId, token]);

  const handleExecuteAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeAction || !selectedAppId || !token) return;

    setSubmittingAction(true);
    setActionSuccessMsg(null);

    try {
      let body: any = {};
      if (activeAction.action_key.includes('RETURN') || activeAction.action_key.includes('DEFICIENCY')) {
        body = { comments: actionComments || 'Deficiency observation communicated to institution.' };
      } else if (activeAction.action_key.includes('RESUBMIT')) {
        body = { comments: actionComments || 'Institutional clarification and cures resubmitted.' };
      } else if (activeAction.target_stage_key) {
        body = { action: activeAction.target_stage_key, comments: actionComments || `Transitioned to ${activeAction.target_stage_key}` };
      }

      const res = await fetch(activeAction.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Action failed with status ${res.status}`);
      }

      setActionSuccessMsg(`Action "${activeAction.action_label}" committed successfully.`);
      setActiveAction(null);
      setActionComments('');
      await fetchCaseData(selectedAppId);
    } catch (err: any) {
      alert(`Workflow transition failed: ${err.message}`);
    } finally {
      setSubmittingAction(false);
    }
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'CRITICAL':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'MEDIUM':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            to="/applications"
            className="p-1.5 text-slate-500 hover:text-slate-800 bg-white rounded border border-slate-300 transition-colors"
            title="Back to Applications"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Case Accountability & Movement History
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Clear statutory responsibility, SLA countdown, permitted next actions, and SHA-256 audit chain
            </p>
          </div>
        </div>

        {/* Application Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-600 font-medium">Select Case:</label>
          <select
            value={selectedAppId}
            onChange={(e) => setSelectedAppId(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500 max-w-[280px] truncate"
          >
            {applications.map((a) => (
              <option key={a.id} value={a.id}>
                {a.application_no} — {a.institution_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {actionSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 flex items-center justify-between">
          <span>{actionSuccessMsg}</span>
          <button onClick={() => setActionSuccessMsg(null)} className="text-emerald-600 font-bold ml-2">&times;</button>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border">
          Loading case accountability diagnostics...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 rounded-lg border border-rose-200">
          Failed to load case data: {error}
        </div>
      ) : appDetail ? (
        <div className="space-y-6">

          {/* ============================================================== */}
          {/* CORE FEATURE: CASE ACCOUNTABILITY & HANDOFF VIEW                */}
          {/* ============================================================== */}
          {accountability && (
            <div className="bg-white rounded-lg border border-slate-300 shadow-sm overflow-hidden">
              {/* Holding Responsibility Banner */}
              <div className={`p-4 border-b flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                accountability.holding_party === 'WAITING_ON_INSTITUTION'
                  ? 'bg-amber-500/10 border-amber-300 text-amber-900'
                  : 'bg-teal-700 text-white border-teal-800'
              }`}>
                <div className="flex items-center gap-3">
                  {accountability.holding_party === 'WAITING_ON_INSTITUTION' ? (
                    <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center border border-amber-300 flex-shrink-0">
                      <AlertTriangle className="w-5 h-5 text-amber-700" />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-teal-800/80 flex items-center justify-center border border-teal-500/50 flex-shrink-0">
                      <ShieldCheck className="w-5 h-5 text-teal-200" />
                    </div>
                  )}
                  <div>
                    <div className="text-[11px] font-mono tracking-wider uppercase font-semibold opacity-90">
                      Current Holding Responsibility: {accountability.holding_party.replace(/_/g, ' ')}
                    </div>
                    <div className="text-base sm:text-lg font-bold">
                      {accountability.holding_party === 'WAITING_ON_INSTITUTION'
                        ? 'Ball is in Institution’s Court — Action / Deficiency Cure Required'
                        : `Ball is with AICTE — Assigned to ${accountability.holding_responsible_role}`}
                    </div>
                    <div className="text-xs opacity-85 mt-0.5">
                      {accountability.holding_party_label} &bull; Case officer: {accountability.assigned_officer_name || 'Unassigned Scrutiny Pool'}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <span className={`px-2.5 py-1 rounded text-xs font-bold border ${
                    accountability.is_overdue
                      ? 'bg-rose-100 text-rose-800 border-rose-300'
                      : accountability.days_remaining <= 2
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-emerald-100 text-emerald-800 border-emerald-300'
                  }`}>
                    {accountability.is_overdue
                      ? `OVERDUE by ${Math.abs(accountability.days_remaining)} days`
                      : `${accountability.days_remaining} days remaining in SLA`}
                  </span>
                </div>
              </div>

              {/* SLA & Stage Diagnostic Strip */}
              <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-slate-200 bg-slate-50 border-b border-slate-200 text-xs">
                <div className="p-3.5">
                  <div className="text-slate-500 text-[11px]">Current Stage</div>
                  <div className="font-bold text-slate-800 mt-0.5">{accountability.current_stage_name}</div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Entered: {new Date(accountability.stage_entered_at).toLocaleDateString('en-IN')}
                  </div>
                </div>
                <div className="p-3.5">
                  <div className="text-slate-500 text-[11px]">Stage Age vs Statutory SLA</div>
                  <div className="font-bold text-slate-800 mt-0.5">
                    {accountability.days_in_stage}d elapsed / {accountability.sla_limit_days}d limit
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Return count: <strong>{accountability.return_count}x</strong>
                  </div>
                </div>
                <div className="p-3.5">
                  <div className="text-slate-500 text-[11px]">Explainable Urgency Score</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="font-bold text-slate-900 text-sm">{accountability.attention_score}/100</span>
                    <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold border ${getTierBadge(accountability.attention_tier)}`}>
                      {accountability.attention_tier}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">Deterministic Attention Engine</div>
                </div>
                <div className="p-3.5">
                  <div className="text-slate-500 text-[11px]">Cryptographic Proof (INV-02)</div>
                  <div className="font-mono text-emerald-700 font-semibold mt-0.5 truncate" title={accountability.latest_audit_hash || 'Genesis'}>
                    SHA-256: {accountability.latest_audit_hash ? accountability.latest_audit_hash.substring(0, 14) + '...' : 'Genesis Chain'}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {accountability.audit_event_count} Immutable Audit Blocks
                  </div>
                </div>
              </div>

              {/* Persona Context & Action Permissibility */}
              <div className="p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-slate-100 p-3 rounded-md border border-slate-200">
                  <div className="flex items-center gap-2 text-xs text-slate-700">
                    <User className="w-4 h-4 text-slate-500" />
                    <span>Your Active Persona: <strong>{user?.full_name}</strong> &bull; Role: <strong>{user?.role}</strong></span>
                  </div>
                  <div>
                    {accountability.current_user_can_act ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded border border-emerald-300">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        Authorized to Execute Next Action
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-200 text-slate-700 text-xs font-medium rounded border border-slate-300">
                        <Lock className="w-3.5 h-3.5 text-slate-500" />
                        Observer Mode: Responsibility Rests with {accountability.holding_responsible_role}
                      </span>
                    )}
                  </div>
                </div>

                {/* Permitted Next Actions Table / Cards */}
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-teal-600" /> Statutory Permitted Next Actions for Current Stage
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {accountability.permitted_next_actions.map((pa) => (
                      <div
                        key={pa.action_key}
                        className={`p-3.5 rounded-lg border text-xs space-y-2 transition-all ${
                          pa.is_permitted_for_user
                            ? 'bg-teal-50/50 border-teal-300 ring-1 ring-teal-200'
                            : 'bg-slate-50 border-slate-200 opacity-75'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                              {pa.action_label}
                              {pa.is_permitted_for_user ? (
                                <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded font-semibold border border-emerald-300">
                                  Permitted for You
                                </span>
                              ) : (
                                <span className="text-[10px] bg-slate-200 text-slate-600 px-1.5 py-0.2 rounded font-medium">
                                  Role Restricted
                                </span>
                              )}
                            </div>
                            <p className="text-slate-600 text-[11px] mt-1">{pa.description}</p>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-slate-200/80">
                          <div className="text-[10px] text-slate-500">
                            Required Role(s): <span className="font-mono text-slate-700">{pa.allowed_roles.join(', ')}</span>
                          </div>

                          {pa.is_permitted_for_user ? (
                            <button
                              onClick={() => {
                                setActiveAction(pa);
                                setActionComments('');
                              }}
                              className="inline-flex items-center gap-1 px-3 py-1 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded text-xs shadow-sm transition-colors"
                            >
                              Execute <ArrowRight className="w-3 h-3" />
                            </button>
                          ) : (
                            <span className="text-[11px] text-slate-400 italic flex items-center gap-1">
                              <Lock className="w-3 h-3" /> Requires {pa.allowed_roles[0]}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Attention Factors & Blockers */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {/* Attention Factors Breakdown */}
                  <div className="bg-slate-50 p-3.5 rounded border border-slate-200 text-xs">
                    <h5 className="font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" /> Active Attention Scoring Drivers
                    </h5>
                    {accountability.attention_factors.length > 0 ? (
                      <ul className="space-y-1.5 text-slate-600">
                        {accountability.attention_factors.map((f, fIdx) => (
                          <li key={fIdx} className="flex items-start gap-1.5">
                            <span className="text-teal-600 font-bold">&bull;</span>
                            <span>{f}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-slate-500 italic">No adverse urgency factors; application progressing within standard SLA.</div>
                    )}
                  </div>

                  {/* Dependencies & Blockers */}
                  <div className="bg-slate-50 p-3.5 rounded border border-slate-200 text-xs">
                    <h5 className="font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-600" /> Statutory Undertakings & Document Registry
                    </h5>
                    {accountability.blockers.length > 0 ? (
                      <div className="space-y-1.5">
                        {accountability.blockers.map((b, bIdx) => (
                          <div key={bIdx} className="p-2 bg-white rounded border border-slate-200 flex items-start justify-between gap-2">
                            <div>
                              <div className="font-semibold text-slate-800">{b.title}</div>
                              <div className="text-[11px] text-slate-500">{b.detail}</div>
                            </div>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                              b.status === 'OVERDUE' || b.status === 'EXPIRED'
                                ? 'bg-rose-100 text-rose-800 border-rose-300'
                                : 'bg-amber-100 text-amber-800 border-amber-300'
                            }`}>
                              {b.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-slate-500 italic">All statutory land deeds, safety NOCs, and condition undertakings are in order.</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Case Summary Card */}
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-3 mb-4">
              <div>
                <span className="text-xs font-mono bg-slate-100 text-slate-700 px-2 py-0.5 rounded border">
                  {appDetail.route}
                </span>
                <div className="flex items-center gap-2 mt-1">
                  <h3 className="text-lg font-bold text-slate-900 font-mono">
                    {appDetail.application_no}
                  </h3>
                  <DataTrustBadge
                    sourceSystem={appDetail.source_system || accountability?.source_system}
                    isSynthetic={appDetail.is_synthetic ?? accountability?.is_synthetic}
                  />
                </div>
                <p className="text-xs text-slate-600">
                  {appDetail.institution_name} &bull; {appDetail.region_name}
                </p>
              </div>
              <div className="text-right">
                <span className="text-xs font-semibold px-2.5 py-1 rounded bg-teal-50 text-teal-800 border border-teal-200">
                  Current Status: {appDetail.current_stage_name || appDetail.status}
                </span>
                <div className="text-[11px] text-slate-500 mt-1">
                  Stage Age: <strong>{appDetail.days_in_stage} days</strong> &bull; Total Pipeline Age: {appDetail.total_days} days
                </div>
              </div>
            </div>

            <div className="text-xs text-slate-600 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded border">
              <div>
                <span className="text-slate-400 block">Application Type:</span>
                <span className="font-medium text-slate-800">{appDetail.application_type}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Academic Session:</span>
                <span className="font-medium text-slate-800">{appDetail.academic_year}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Processing Model:</span>
                <span className="font-medium text-slate-800">Deterministic FSM</span>
              </div>
              <div>
                <span className="text-slate-400 block">Audit Integrity:</span>
                <span className="font-semibold text-emerald-700">SHA-256 Chained</span>
              </div>
            </div>
          </div>

          {/* Chronological Vertical Timeline */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
            <h4 className="font-bold text-sm text-slate-800 mb-6 flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-teal-600" /> Chronological Movement Ledger
            </h4>

            <div className="relative pl-6 space-y-8 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {appDetail.history && appDetail.history.length > 0 ? (
                appDetail.history.map((h, idx) => (
                  <div key={h.id || idx} className="relative group">
                    <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-teal-600 border-2 border-white shadow"></div>
                    <div className="bg-slate-50 border border-slate-200 rounded p-4 text-xs space-y-1.5 hover:border-teal-300 transition-colors">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900 text-sm">
                          {h.action.replace(/_/g, ' ')}
                        </span>
                        <span className="text-slate-400 font-mono text-[11px]">
                          {new Date(h.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                        </span>
                      </div>

                      <div className="text-slate-600 flex items-center gap-2">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>Actor: <strong>{h.actor_name}</strong> ({h.actor_role})</span>
                      </div>

                      {h.from_stage && h.to_stage && (
                        <div className="text-slate-500 font-mono text-[11px]">
                          {h.from_stage} &rarr; {h.to_stage}
                        </div>
                      )}

                      {h.comments && (
                        <div className="mt-2 p-2.5 bg-white rounded border border-slate-200 text-slate-700 italic">
                          "{h.comments}"
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500">No movement history recorded yet.</div>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {/* Action Execution Modal */}
      {activeAction && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b pb-2">
              <h3 className="font-bold text-sm text-slate-900">
                Execute Statutory Action: {activeAction.action_label}
              </h3>
              <button
                onClick={() => setActiveAction(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <div className="text-xs text-slate-600 space-y-2">
              <p>{activeAction.description}</p>
              {activeAction.target_stage_key && (
                <div className="p-2 bg-slate-50 border rounded font-mono text-[11px]">
                  Target Milestone: <strong>{activeAction.target_stage_key}</strong>
                </div>
              )}
            </div>

            <form onSubmit={handleExecuteAction} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Statutory Remarks / Mandatory Deficiency Comments:
                </label>
                <textarea
                  required={activeAction.action_key.includes('RETURN')}
                  rows={3}
                  value={actionComments}
                  onChange={(e) => setActionComments(e.target.value)}
                  placeholder={
                    activeAction.action_key.includes('RETURN')
                      ? 'Detailed statutory reasons for deficiency return (Mandatory per APH)...'
                      : 'Record regulatory observations, committee approval reference, or notes...'
                  }
                  className="w-full text-xs p-2.5 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveAction(null)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded border border-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingAction}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50 rounded shadow-sm"
                >
                  {submittingAction ? 'Committing...' : 'Confirm & Commit Action'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
