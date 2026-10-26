import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Clock, 
  Building2, 
  RotateCcw,
  ShieldCheck,
  Flame,
  FileCheck,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  Upload,
  Calendar,
  Eye,
  Award
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
  stage_distribution?: { stage_key: string; stage: string; count: number }[];
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
  role_view?: Record<string, any>;
}

const ROUTE_COLORS = ['#0f766e', '#0284c7', '#8b5cf6', '#f59e0b'];

export const DashboardPage: React.FC = () => {
  const { user, token } = useAuth();
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

  // Stage funnel data formatting (prefers structured stage_distribution, falls back to stage_breakdown)
  const stageData = useMemo(() => {
    if (!stats) return [];
    if (stats.stage_distribution && stats.stage_distribution.length > 0) {
      return stats.stage_distribution.map((item) => ({
        stage: item.stage,
        count: Number(item.count) || 0
      }));
    }
    const sb = stats.stage_breakdown || {};
    return [
      { stage: 'Draft', count: sb['DRAFT'] ?? sb['Draft'] ?? 0 },
      { stage: 'Submitted', count: sb['SUBMITTED'] ?? sb['Submitted'] ?? 0 },
      { stage: 'Scrutiny', count: sb['SCRUTINY'] ?? sb['Scrutiny'] ?? 0 },
      { stage: 'EVC Visit', count: sb['EVC'] ?? sb['EVC Visit'] ?? 0 },
      { stage: 'SAC / SHC', count: sb['SAC_SHC'] ?? sb['SAC / SHC'] ?? 0 },
      { stage: 'Final Decision', count: sb['DECISION'] ?? sb['Final Decision'] ?? 0 }
    ];
  }, [stats]);

  const totalStageCount = useMemo(() => {
    return stageData.reduce((acc, curr) => acc + curr.count, 0);
  }, [stageData]);

  const roleView = stats?.role_view || {};
  const userRole = user?.role || '';
  const isInstAdmin = userRole === 'INST_ADMIN';
  const isRegionalRole = ['RO_OFFICER', 'REGIONAL_DIR'].includes(userRole);
  const isEvcCoord = userRole === 'EVC_COORD';
  const isCommitteeMember = ['COMM_MEMBER', 'COMMITTEE_MBR'].includes(userRole);
  const isCompReviewer = ['COMP_REVIEW', 'COMP_REV'].includes(userRole);
  const isCompAuth = userRole === 'COMP_AUTH';
  const isBureauOfficer = ['BO_OFFICER', 'BUREAU_OFFICER'].includes(userRole);

  const showRegionalWorkload = stats && 
    stats.regional_workload && 
    stats.regional_workload.length > 0 && 
    !isInstAdmin && 
    !isCommitteeMember;

  return (
    <div className="space-y-6">
      {/* Title & Role Context Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-teal-800 text-teal-200">
              {roleView.role_title || userRole || 'Authenticated'}
            </span>
            {isInstAdmin && roleView.institution_name && (
              <span className="text-xs text-slate-600 font-medium truncate max-w-[280px]">
                · {roleView.institution_name}
              </span>
            )}
            {isRegionalRole && roleView.region_name && (
              <span className="text-xs text-slate-600 font-medium">
                · {roleView.region_name}
              </span>
            )}
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            {isInstAdmin ? 'Institution Action Center' : 'AICTE Operations Dashboard (Live Metrics)'}
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            {isInstAdmin 
              ? 'Institutional compliance undertakings, deficiency notices, and application progression' 
              : 'Real-time pendency tracking, stage progression, regional workload, and compliance health'}
          </p>
        </div>

        <button
          onClick={fetchStats}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded shadow-sm transition-colors shrink-0"
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
                <span>{isInstAdmin ? 'My Applications' : 'Total Applications'}</span>
                <FileText className="w-4 h-4 text-teal-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-2">{stats.summary.total_applications}</div>
              <div className="text-[11px] text-teal-700 font-medium mt-1">
                {stats.summary.active_applications} In Active Progress
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Critical Alerts</span>
                <Flame className="w-4 h-4 text-rose-600" />
              </div>
              <div className="text-2xl font-bold text-rose-600 mt-2">{stats.summary.critical_alerts}</div>
              <div className="text-[11px] text-rose-700 font-medium mt-1">
                {stats.summary.escalated_alerts} Escalated
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                <span>Deficiencies / Holds</span>
                <Clock className="w-4 h-4 text-amber-600" />
              </div>
              <div className="text-2xl font-bold text-amber-600 mt-2">{stats.summary.clarification_pending}</div>
              <div className="text-[11px] text-amber-700 font-medium mt-1">
                {isInstAdmin ? 'Action Required' : 'Awaiting Clarification'}
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

          {/* ========================================================= */}
          {/* ROLE-SPECIFIC WORKSPACE SECTION                            */}
          {/* ========================================================= */}

          {/* 1. INSTITUTION ADMIN WORKSPACE */}
          {isInstAdmin && (
            <div className="space-y-5">
              {/* Deficiency Notices Alert Box */}
              {roleView.deficiency_notices && roleView.deficiency_notices.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      <span>Deficiency Notices Requiring Immediate Resubmission ({roleView.deficiency_notices.length})</span>
                    </div>
                    <span className="text-xs text-amber-700 font-medium">SLA Invariant Inv-03</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {roleView.deficiency_notices.map((d: any) => (
                      <div key={d.id} className="bg-white p-3 rounded border border-amber-200 flex items-center justify-between shadow-xs">
                        <div>
                          <div className="font-bold text-xs text-slate-900">{d.application_no}</div>
                          <div className="text-[11px] text-slate-500">
                            {d.current_stage} · Return Cycle #{d.return_count}
                          </div>
                          {d.sla_deadline && (
                            <div className="text-[10px] text-amber-700 font-mono mt-0.5">
                              Due: {new Date(d.sla_deadline).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                        <Link
                          to={`/applications`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded transition-colors"
                        >
                          <span>Respond</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Grid: Pending Compliance & Document Expiries */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Pending Compliance Undertakings */}
                <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b pb-2">
                    <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-teal-600" /> Pending Compliance Undertakings
                    </h3>
                    <Link to="/compliance" className="text-xs text-teal-600 hover:text-teal-800 font-medium">
                      View All
                    </Link>
                  </div>
                  {roleView.pending_compliance && roleView.pending_compliance.length > 0 ? (
                    <div className="space-y-2">
                      {roleView.pending_compliance.slice(0, 5).map((ob: any) => (
                        <div key={ob.id} className="p-2.5 bg-slate-50 rounded border border-slate-100 flex items-center justify-between text-xs">
                          <div className="truncate mr-2">
                            <div className="font-semibold text-slate-800 truncate">{ob.title}</div>
                            <div className="text-[10px] text-slate-400 font-mono">Category: {ob.category}</div>
                          </div>
                          <div className="shrink-0 flex items-center gap-2">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              ob.days_remaining < 0 ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-800'
                            }`}>
                              {ob.days_remaining < 0 ? `${Math.abs(ob.days_remaining)}d overdue` : `${ob.days_remaining}d left`}
                            </span>
                            <Link to="/compliance" className="text-teal-600 hover:text-teal-800">
                              <Upload className="w-3.5 h-3.5" />
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-400">All compliance undertakings are in order</div>
                  )}
                </div>

                {/* Prescribed Documents & Expiry Reminders */}
                <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b pb-2">
                    <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                      <FileCheck className="w-4 h-4 text-purple-600" /> Prescribed Document Reminders
                    </h3>
                    <Link to="/documents" className="text-xs text-teal-600 hover:text-teal-800 font-medium">
                      View Registry
                    </Link>
                  </div>
                  {roleView.document_reminders && roleView.document_reminders.length > 0 ? (
                    <div className="space-y-2">
                      {roleView.document_reminders.slice(0, 5).map((d: any) => (
                        <div key={d.id} className="p-2.5 bg-slate-50 rounded border border-slate-100 flex items-center justify-between text-xs">
                          <div className="truncate mr-2">
                            <div className="font-semibold text-slate-800 truncate">{d.title}</div>
                            <div className="text-[10px] text-slate-400 font-mono">Expires: {d.expiry_date}</div>
                          </div>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                            d.status === 'EXPIRED' ? 'bg-rose-100 text-rose-700' : 'bg-purple-100 text-purple-800'
                          }`}>
                            {d.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-400">No expiring deeds or NOCs</div>
                  )}
                </div>
              </div>

              {/* My Applications Quick Table */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b pb-2">
                  <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <FileText className="w-4 h-4 text-teal-600" /> My Institution Applications
                  </h3>
                  <Link to="/applications" className="text-xs text-teal-600 hover:text-teal-800 font-medium">
                    All Applications
                  </Link>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                        <th className="py-2.5 px-3">Application No</th>
                        <th className="py-2.5 px-3">Route</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3">Stage</th>
                        <th className="py-2.5 px-3">Submitted</th>
                        <th className="py-2.5 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {roleView.my_applications && roleView.my_applications.length > 0 ? (
                        roleView.my_applications.map((app: any) => (
                          <tr key={app.id} className="hover:bg-slate-50">
                            <td className="py-2 px-3 font-bold text-slate-900">{app.application_no}</td>
                            <td className="py-2 px-3 font-mono text-teal-700">{app.route}</td>
                            <td className="py-2 px-3">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">
                                {app.status}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-slate-600">{app.stage_name}</td>
                            <td className="py-2 px-3 text-slate-400 font-mono text-[11px]">
                              {app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : 'N/A'}
                            </td>
                            <td className="py-2 px-3 text-right">
                              <Link to={`/timeline`} className="text-teal-600 hover:text-teal-800 inline-flex items-center gap-1 font-semibold">
                                <Eye className="w-3.5 h-3.5" />
                                <span>Track</span>
                              </Link>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={6} className="py-6 text-center text-slate-400">
                            No applications submitted yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* 2. REGIONAL OFFICER & REGIONAL DIRECTOR WORKSPACE */}
          {isRegionalRole && (
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <div>
                  <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-teal-700" /> Regional Scrutiny Queue
                  </h3>
                  <p className="text-xs text-slate-500">Cases actively requiring scrutiny review within assigned jurisdiction</p>
                </div>
                <Link to="/applications" className="text-xs text-teal-600 hover:text-teal-800 font-medium">
                  Open Full Queue
                </Link>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                      <th className="py-2.5 px-3">Application No</th>
                      <th className="py-2.5 px-3">Institution</th>
                      <th className="py-2.5 px-3">Route</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Stage Age</th>
                      <th className="py-2.5 px-3">Returns</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {roleView.scrutiny_queue && roleView.scrutiny_queue.length > 0 ? (
                      roleView.scrutiny_queue.map((app: any) => (
                        <tr key={app.id} className="hover:bg-slate-50">
                          <td className="py-2.5 px-3 font-bold text-slate-900">{app.application_no}</td>
                          <td className="py-2.5 px-3 font-medium text-slate-800 max-w-xs truncate">{app.institution_name}</td>
                          <td className="py-2.5 px-3 font-mono text-teal-700">{app.route}</td>
                          <td className="py-2.5 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-800">
                              {app.status}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-slate-600 font-semibold">{app.stage_age_days}d in stage</td>
                          <td className="py-2.5 px-3 text-slate-500">{app.return_count}</td>
                          <td className="py-2.5 px-3 text-right">
                            <Link to="/applications" className="px-2 py-1 text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 rounded">
                              Scrutinize
                            </Link>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7} className="py-6 text-center text-slate-400">
                          Scrutiny queue is clear. No pending applications in assigned region.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 3. EVC COORDINATOR WORKSPACE */}
          {isEvcCoord && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b pb-2">
                  <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-teal-600" /> Awaiting Inspection Scheduling
                  </h3>
                  <Link to="/evc" className="text-xs text-teal-600 hover:text-teal-800 font-medium">Manage EVC</Link>
                </div>
                {roleView.awaiting_schedule && roleView.awaiting_schedule.length > 0 ? (
                  <div className="space-y-2">
                    {roleView.awaiting_schedule.map((v: any) => (
                      <div key={v.visit_id} className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between text-xs">
                        <div>
                          <div className="font-bold text-slate-900">{v.application_no}</div>
                          <div className="text-[11px] text-slate-600 truncate max-w-xs">{v.institution_name}</div>
                        </div>
                        <Link to="/evc" className="px-2 py-1 text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 rounded">
                          Schedule Visit
                        </Link>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-xs text-slate-400">No visits awaiting schedule</div>
                )}
              </div>

              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b pb-2">
                  <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-purple-600" /> Pending Inspection Reports
                  </h3>
                  <Link to="/evc" className="text-xs text-teal-600 hover:text-teal-800 font-medium">View All</Link>
                </div>
                {roleView.pending_reports && roleView.pending_reports.length > 0 ? (
                  <div className="space-y-2">
                    {roleView.pending_reports.map((v: any) => (
                      <div key={v.visit_id} className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between text-xs">
                        <div>
                          <div className="font-bold text-slate-900">{v.application_no}</div>
                          <div className="text-[11px] text-slate-600 truncate max-w-xs">{v.institution_name}</div>
                        </div>
                        <span className="text-[11px] font-mono text-purple-700 font-semibold">Report Pending</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-xs text-slate-400">All completed visits have submitted reports</div>
                )}
              </div>
            </div>
          )}

          {/* 4. COMMITTEE MEMBER WORKSPACE */}
          {isCommitteeMember && (
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <div>
                  <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-teal-700" /> My Assigned Inspection Visits
                  </h3>
                  <p className="text-xs text-slate-500">Expert visit roster and report submission responsibilities</p>
                </div>
                <Link to="/evc" className="text-xs text-teal-600 hover:text-teal-800 font-medium">EVC Hub</Link>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                      <th className="py-2.5 px-3">Application No</th>
                      <th className="py-2.5 px-3">Institution</th>
                      <th className="py-2.5 px-3">Scheduled Date</th>
                      <th className="py-2.5 px-3">Visit Status</th>
                      <th className="py-2.5 px-3">Report Status</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {roleView.assigned_inspections && roleView.assigned_inspections.length > 0 ? (
                      roleView.assigned_inspections.map((v: any) => (
                        <tr key={v.visit_id} className="hover:bg-slate-50">
                          <td className="py-2.5 px-3 font-bold text-slate-900">{v.application_no}</td>
                          <td className="py-2.5 px-3 font-medium text-slate-800 max-w-xs truncate">{v.institution_name}</td>
                          <td className="py-2.5 px-3 font-mono text-teal-700">{v.confirmed_date}</td>
                          <td className="py-2.5 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">
                              {v.status}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            {v.report_submitted ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                                Submitted
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                                Pending Report
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <Link to="/evc" className="px-2.5 py-1 text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 rounded">
                              View Visit
                            </Link>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-6 text-center text-slate-400">
                          You have no assigned inspection visits at this time.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 5. COMPLIANCE REVIEWER WORKSPACE */}
          {isCompReviewer && (
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <div>
                  <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" /> Evidence Awaiting Verification
                  </h3>
                  <p className="text-xs text-slate-500">Submitted institutional undertakings requiring statutory verification</p>
                </div>
                <Link to="/compliance" className="text-xs text-teal-600 hover:text-teal-800 font-medium">Compliance Review Hub</Link>
              </div>

              {roleView.evidence_awaiting_verification && roleView.evidence_awaiting_verification.length > 0 ? (
                <div className="space-y-2">
                  {roleView.evidence_awaiting_verification.map((ev: any) => (
                    <div key={ev.evidence_id} className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-bold text-slate-900">{ev.obligation_title}</div>
                        <div className="text-[11px] text-slate-600">
                          {ev.institution_name} · File: <span className="font-mono">{ev.file_name}</span>
                        </div>
                      </div>
                      <Link to="/compliance" className="px-2.5 py-1 text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-800 rounded">
                        Verify Evidence
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center text-xs text-slate-400">No evidence awaiting review</div>
              )}
            </div>
          )}

          {/* 6. COMPETENT AUTHORITY WORKSPACE */}
          {isCompAuth && (
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <div>
                  <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <Award className="w-4 h-4 text-amber-600" /> Statutory Council Decision Queue
                  </h3>
                  <p className="text-xs text-slate-500">
                    Applications recommended by SAC / SHC awaiting final Competent Authority determination
                  </p>
                </div>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                  Exclusive Statutory Power
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                      <th className="py-2.5 px-3">Application No</th>
                      <th className="py-2.5 px-3">Institution</th>
                      <th className="py-2.5 px-3">Region</th>
                      <th className="py-2.5 px-3">Route</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3 text-right">Statutory Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {roleView.awaiting_statutory_decision && roleView.awaiting_statutory_decision.length > 0 ? (
                      roleView.awaiting_statutory_decision.map((app: any) => (
                        <tr key={app.id} className="hover:bg-slate-50">
                          <td className="py-2.5 px-3 font-bold text-slate-900">{app.application_no}</td>
                          <td className="py-2.5 px-3 font-medium text-slate-800 max-w-xs truncate">{app.institution_name}</td>
                          <td className="py-2.5 px-3 text-slate-600">{app.region_name}</td>
                          <td className="py-2.5 px-3 font-mono text-teal-700">{app.route}</td>
                          <td className="py-2.5 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                              {app.status}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <Link to="/applications" className="px-2.5 py-1 text-xs font-semibold text-white bg-teal-800 hover:bg-teal-900 rounded">
                              Decide
                            </Link>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-6 text-center text-slate-400">
                          No applications currently awaiting final statutory council determination.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 7. BUREAU OFFICER NATIONAL OVERSIGHT */}
          {isBureauOfficer && roleView.national_summary && (
            <div className="bg-slate-900 text-slate-100 p-4 rounded-lg flex items-center justify-between">
              <div>
                <h4 className="font-bold text-sm text-teal-300">National AICTE Bureau Operational Oversight</h4>
                <p className="text-xs text-slate-400">Full cross-regional monitoring of active processing workloads and bottlenecks</p>
              </div>
              <div className="flex gap-4 text-xs font-mono">
                <div><span className="text-slate-400">Active: </span><span className="font-bold text-teal-400">{roleView.national_summary.total_active_national}</span></div>
                <div><span className="text-slate-400">Critical Alerts: </span><span className="font-bold text-rose-400">{roleView.national_summary.critical_national_alerts}</span></div>
                <div><span className="text-slate-400">Overdue Obligations: </span><span className="font-bold text-amber-400">{roleView.national_summary.overdue_undertakings_national}</span></div>
              </div>
            </div>
          )}

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Stage Progression Bar Chart */}
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-teal-600" /> Stage Pipeline Distribution
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">
                  {loading ? 'Querying...' : `${totalStageCount} active in scope`}
                </span>
              </div>
              <div className="h-64 w-full">
                {loading ? (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400">
                    <span className="animate-pulse">Loading stage metrics...</span>
                  </div>
                ) : error ? (
                  <div className="h-full flex items-center justify-center text-xs text-rose-500">
                    Failed to load stage data: {error}
                  </div>
                ) : totalStageCount === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400 p-4 text-center">
                    <TrendingUp className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-xs font-semibold text-slate-600">No applications in these stages</p>
                    <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
                      There are currently no active applications progressing through approval stages for this authorized scope.
                    </p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stageData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                      <XAxis 
                        dataKey="stage" 
                        tick={{ fontSize: 11, fill: '#475569' }} 
                        interval={0} 
                        angle={-15} 
                        textAnchor="end" 
                      />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                      <Tooltip 
                        formatter={(val: any) => [`${val} application${val === 1 ? '' : 's'}`, 'Volume']}
                        labelFormatter={(lbl: string) => `Stage: ${lbl}`}
                        contentStyle={{ 
                          backgroundColor: '#0f172a', 
                          borderColor: '#1e293b', 
                          borderRadius: '6px', 
                          color: '#f8fafc', 
                          fontSize: '12px' 
                        }}
                        itemStyle={{ color: '#2dd4bf' }}
                      />
                      <Bar dataKey="count" fill="#0f766e" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
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

          {/* Regional Workload Table (Strictly Hidden for Institution Admins & Committee Members) */}
          {showRegionalWorkload && (
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-teal-700" /> 
                  {stats.regional_workload.length === 1 
                    ? `Regional Office Workload (${stats.regional_workload[0].region_name})` 
                    : 'Regional Workload & Overdue Allocation'}
                </h3>
                <span className="text-[11px] text-slate-400">
                  {stats.regional_workload.length === 1 ? 'Assigned Jurisdiction' : `${stats.regional_workload.length} Geographic AICTE Regions`}
                </span>
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
          )}
        </>
      ) : null}
    </div>
  );
};
