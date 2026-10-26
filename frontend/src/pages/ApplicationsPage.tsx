import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  CheckCircle, 
  Clock, 
  RotateCcw,
  Eye,
  Send
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface ApplicationItem {
  id: string;
  application_no: string;
  institution_name: string;
  institution_aicte_id: string;
  region_name: string;
  academic_year: string;
  application_type: string;
  route: string;
  status: string;
  current_stage_name: string;
  assigned_officer_name: string | null;
  days_in_stage: number;
  total_days: number;
  return_count: number;
  current_sla_deadline: string | null;
}

export const ApplicationsPage: React.FC = () => {
  const { user, token } = useAuth();
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [routeFilter, setRouteFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Action modal state
  const [actionModal, setActionModal] = useState<{
    open: boolean;
    app: ApplicationItem | null;
    actionType: 'transition' | 'return' | 'resubmit';
    targetStage?: string;
  }>({ open: false, app: null, actionType: 'transition' });
  const [modalComments, setModalComments] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchApplications = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      let url = '/api/applications?';
      if (routeFilter) url += `route=${encodeURIComponent(routeFilter)}&`;
      if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}&`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setApplications(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [token, routeFilter, statusFilter]);

  const handleActionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionModal.app || !token) return;
    setSubmitting(true);

    try {
      let endpoint = '';
      let body: any = {};

      if (actionModal.actionType === 'return') {
        endpoint = `/api/applications/${actionModal.app.id}/return`;
        body = { comments: modalComments };
      } else if (actionModal.actionType === 'resubmit') {
        endpoint = `/api/applications/${actionModal.app.id}/resubmit`;
        body = { comments: modalComments };
      } else {
        endpoint = `/api/applications/${actionModal.app.id}/transition`;
        body = { action: actionModal.targetStage, comments: modalComments };
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Action failed');
      }

      setActionModal({ open: false, app: null, actionType: 'transition' });
      setModalComments('');
      await fetchApplications();
    } catch (err: any) {
      alert(`Workflow error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredApps = applications.filter((app) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      app.application_no.toLowerCase().includes(q) ||
      (app.institution_name && app.institution_name.toLowerCase().includes(q))
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'REJECTED':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'SCRUTINY_DEFICIENT':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'EVC_QUEUE':
      case 'EVC_SCHEDULED':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'DECISION_PENDING':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Applications & Workflow Tracking
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Real-time multi-route approval processing and stage-wise SLA monitoring
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by App No or Institution..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs sm:text-sm border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-500 shrink-0" />
          <select
            value={routeFilter}
            onChange={(e) => setRouteFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Routes</option>
            <option value="ROUTE_A">Route A: Only Scrutiny</option>
            <option value="ROUTE_B">Route B: Scrutiny + EVC</option>
            <option value="ROUTE_C">Route C: EVC + SAC/SHC</option>
            <option value="ROUTE_D">Route D: Only EVC</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="UNDER_SCRUTINY">Under Scrutiny</option>
            <option value="SCRUTINY_DEFICIENT">Clarification Requested</option>
            <option value="SCRUTINY_RECOMMENDED">Scrutiny Cleared</option>
            <option value="EVC_QUEUE">EVC Queue</option>
            <option value="EVC_SCHEDULED">EVC Scheduled</option>
            <option value="DECISION_PENDING">Decision Pending</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>

          <button
            onClick={fetchApplications}
            className="px-3 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded border border-slate-300 transition-colors"
          >
            Apply
          </button>
        </div>
      </div>

      {/* Applications Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">
            Loading workflow applications...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 bg-rose-50">
            Error: {error}
          </div>
        ) : filteredApps.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No applications found matching the selected filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs sm:text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 text-xs uppercase font-semibold">
                  <th className="py-3 px-4">Application Details</th>
                  <th className="py-3 px-4">Institution & Region</th>
                  <th className="py-3 px-4">Route</th>
                  <th className="py-3 px-4">Current Stage & Age</th>
                  <th className="py-3 px-4">Assigned Officer</th>
                  <th className="py-3 px-4 text-right">Permitted Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredApps.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-mono font-bold text-slate-900">{app.application_no}</div>
                      <div className="text-[11px] text-slate-500">{app.application_type} ({app.academic_year})</div>
                      {app.return_count > 0 && (
                        <span className="inline-flex items-center text-[10px] font-medium text-amber-700 bg-amber-50 border border-amber-200 px-1.5 py-0.2 rounded mt-0.5">
                          Returned {app.return_count}x
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800 line-clamp-1">{app.institution_name}</div>
                      <div className="text-[11px] text-slate-500">{app.region_name} &bull; {app.institution_aicte_id}</div>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs">
                      <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                        {app.route}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getStatusBadge(app.status)}`}>
                        {app.current_stage_name || app.status}
                      </span>
                      <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>Stage: <strong>{app.days_in_stage}d</strong></span>
                        <span>&bull; Total: {app.total_days}d</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-700">
                      {app.assigned_officer_name ? (
                        <span className="font-medium">{app.assigned_officer_name}</span>
                      ) : (
                        <span className="text-amber-600 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                          Unassigned
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right space-x-1">
                      {/* Permitted contextual action buttons depending on active persona role and stage */}
                      {user?.role === 'RO_OFFICER' && app.status === 'UNDER_SCRUTINY' && (
                        <>
                          <button
                            onClick={() => setActionModal({ open: true, app, actionType: 'return' })}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded"
                            title="Return for Deficiency"
                          >
                            <RotateCcw className="w-3 h-3" /> Return
                          </button>
                          <button
                            onClick={() => setActionModal({ open: true, app, actionType: 'transition', targetStage: app.route === 'ROUTE_A' ? 'SCRUTINY_RECOMMENDED' : 'EVC_QUEUE' })}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 rounded"
                            title="Clear Scrutiny"
                          >
                            <CheckCircle className="w-3 h-3" /> Clear
                          </button>
                        </>
                      )}

                      {user?.role === 'INST_ADMIN' && app.status === 'SCRUTINY_DEFICIENT' && (
                        <button
                          onClick={() => setActionModal({ open: true, app, actionType: 'resubmit' })}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm"
                        >
                          <Send className="w-3 h-3" /> Resubmit Clarification
                        </button>
                      )}

                      {user?.role === 'COMP_AUTH' && app.status === 'DECISION_PENDING' && (
                        <>
                          <button
                            onClick={() => setActionModal({ open: true, app, actionType: 'transition', targetStage: 'APPROVED' })}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded shadow-sm"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => setActionModal({ open: true, app, actionType: 'transition', targetStage: 'REJECTED' })}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded shadow-sm"
                          >
                            Reject
                          </button>
                        </>
                      )}

                      <a
                        href={`/timeline?app_id=${app.id}`}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold text-teal-800 bg-teal-50 hover:bg-teal-100 border border-teal-300 rounded shadow-xs transition-colors"
                        title="View Case Accountability & Handoff View"
                      >
                        <Eye className="w-3.5 h-3.5 text-teal-600" />
                        <span>Accountability & Handoff</span>
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Dialog for Workflow Actions */}
      {actionModal.open && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b pb-2">
              <h3 className="font-bold text-slate-900 text-sm sm:text-base">
                {actionModal.actionType === 'return' ? 'Return Application for Deficiency (INV-02)' :
                 actionModal.actionType === 'resubmit' ? 'Resubmit Clarification Notes' :
                 `Transition Application: ${actionModal.targetStage}`}
              </h3>
            </div>

            <div className="text-xs text-slate-600">
              <p>Application: <strong className="font-mono">{actionModal.app?.application_no}</strong></p>
              <p>Institution: <strong>{actionModal.app?.institution_name}</strong></p>
            </div>

            <form onSubmit={handleActionSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {actionModal.actionType === 'return' ? 'Deficiency Reason (Mandatory)*' : 'Reviewer / Action Notes*'}
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder={
                    actionModal.actionType === 'return'
                      ? 'Specify exact document deficiency, missing clearance, or regulation clause...'
                      : 'Enter administrative observations or justification...'
                  }
                  value={modalComments}
                  onChange={(e) => setModalComments(e.target.value)}
                  className="w-full text-xs sm:text-sm p-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActionModal({ open: false, app: null, actionType: 'transition' })}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded border border-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm disabled:opacity-50"
                >
                  {submitting ? 'Recording...' : 'Confirm Action'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
