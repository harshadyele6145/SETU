import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Calendar, 
  Search, 
  Filter, 
  Plus, 
  Upload, 
  AlertTriangle, 
  CheckCircle2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface ExpertItem {
  id: string;
  expert_name: string;
  designation: string;
  organization: string;
  contact_email: string;
  status: string;
}

interface EVCVisitItem {
  id: string;
  application_id: string;
  application_no: string;
  institution_name: string;
  region_name: string;
  status: string;
  proposed_date: string | null;
  confirmed_date: string | null;
  completed_date: string | null;
  report_submitted_date: string | null;
  coordinator_id: string | null;
  coordinator_name: string | null;
  delay_reason: string | null;
  report_summary: string | null;
  report_file_ref: string | null;
  experts: ExpertItem[];
  created_at: string;
}

export const EVCManagementPage: React.FC = () => {
  const { user, token } = useAuth();
  const [visits, setVisits] = useState<EVCVisitItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [rescheduleModal, setRescheduleModal] = useState<{ open: boolean; visit: EVCVisitItem | null }>({
    open: false,
    visit: null
  });
  const [newDate, setNewDate] = useState('');
  const [delayReason, setDelayReason] = useState('');
  const [rescheduling, setRescheduling] = useState(false);

  const [expertModal, setExpertModal] = useState<{ open: boolean; visit: EVCVisitItem | null }>({
    open: false,
    visit: null
  });
  const [expertName, setExpertName] = useState('');
  const [expertDesignation, setExpertDesignation] = useState('');
  const [expertOrg, setExpertOrg] = useState('');
  const [expertEmail, setExpertEmail] = useState('');
  const [assigning, setAssigning] = useState(false);

  const [reportModal, setReportModal] = useState<{ open: boolean; visit: EVCVisitItem | null }>({
    open: false,
    visit: null
  });
  const [reportSummary, setReportSummary] = useState('');
  const [reportFile, setReportFile] = useState<File | null>(null);
  const [submittingReport, setSubmittingReport] = useState(false);

  const fetchVisits = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      let url = '/api/evc/visits?';
      if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}&`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setVisits(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch EVC visits');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVisits();
  }, [token, statusFilter]);

  const handleRescheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rescheduleModal.visit || !newDate || !delayReason.trim() || !token) return;
    setRescheduling(true);

    try {
      const res = await fetch(`/api/evc/visits/${rescheduleModal.visit.id}/reschedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          new_date: newDate,
          delay_reason: delayReason
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Rescheduling failed');
      }

      setRescheduleModal({ open: false, visit: null });
      setNewDate('');
      setDelayReason('');
      await fetchVisits();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setRescheduling(false);
    }
  };

  const handleExpertSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!expertModal.visit || !expertName || !token) return;
    setAssigning(true);

    try {
      const res = await fetch(`/api/evc/visits/${expertModal.visit.id}/experts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          expert_name: expertName,
          designation: expertDesignation,
          organization: expertOrg,
          contact_email: expertEmail
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Expert assignment failed');
      }

      setExpertModal({ open: false, visit: null });
      setExpertName('');
      setExpertDesignation('');
      setExpertOrg('');
      setExpertEmail('');
      await fetchVisits();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setAssigning(false);
    }
  };

  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportModal.visit || !reportSummary.trim() || !reportFile || !token) return;
    setSubmittingReport(true);

    try {
      const formData = new FormData();
      formData.append('report_summary', reportSummary);
      formData.append('file', reportFile);

      const res = await fetch(`/api/evc/visits/${reportModal.visit.id}/report`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Report submission failed');
      }

      setReportModal({ open: false, visit: null });
      setReportSummary('');
      setReportFile(null);
      await fetchVisits();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setSubmittingReport(false);
    }
  };

  const filtered = visits.filter((v) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      v.application_no.toLowerCase().includes(q) ||
      v.institution_name.toLowerCase().includes(q) ||
      v.region_name.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'REPORT_SUBMITTED':
      case 'COMPLETED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'SCHEDULED':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'AWAITING_SCHEDULE':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  const canManageEVC = user?.role === 'RO_OFFICER' || user?.role === 'EVC_COORD' || user?.role === 'BO_OFFICER' || user?.role === 'REGIONAL_DIR';

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Expert Visit Committee (EVC) Coordination
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Physical campus inspection scheduling, expert roster management, mandatory delay logging, and report uploads
          </p>
        </div>
      </div>

      {/* Filter Bar */}
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

        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All EVC Statuses</option>
            <option value="AWAITING_SCHEDULE">Awaiting Schedule</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="REPORT_SUBMITTED">Report Submitted</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>
      </div>

      {/* Visits List */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border">
          Loading EVC inspection records...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 rounded-lg border border-rose-200">
          Error: {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border">
          No EVC inspections match your current criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((visit) => (
            <div key={visit.id} className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-teal-800 text-sm">{visit.application_no}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${getStatusBadge(visit.status)}`}>
                      {visit.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="text-xs text-slate-700 font-semibold mt-0.5">{visit.institution_name}</div>
                  <div className="text-[11px] text-slate-500">{visit.region_name}</div>
                </div>

                <div className="text-right text-xs space-y-1">
                  <div>Inspection Date: <strong className="text-slate-900">{visit.confirmed_date || 'Unscheduled'}</strong></div>
                  {visit.coordinator_name && (
                    <div className="text-[11px] text-slate-500">Coordinator: {visit.coordinator_name}</div>
                  )}
                </div>
              </div>

              {/* Delay reason if rescheduled */}
              {visit.delay_reason && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900">
                  <div className="font-bold flex items-center gap-1.5 text-amber-800">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Mandatory Delay Justification Logged:
                  </div>
                  <p className="mt-1 italic">"{visit.delay_reason}"</p>
                </div>
              )}

              {/* Report summary if submitted */}
              {visit.report_summary && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-950">
                  <div className="font-bold flex items-center gap-1.5 text-emerald-800">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    EVC Committee Inspection Findings:
                  </div>
                  <p className="mt-1">{visit.report_summary}</p>
                </div>
              )}

              {/* Expert Roster */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-slate-800 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-teal-700" /> Visiting Experts Roster ({visit.experts.length})
                  </span>
                  {canManageEVC && visit.status !== 'COMPLETED' && (
                    <button
                      onClick={() => setExpertModal({ open: true, visit })}
                      className="inline-flex items-center gap-1 text-[11px] text-teal-700 hover:text-teal-900 font-medium"
                    >
                      <Plus className="w-3.5 h-3.5" /> Assign Expert
                    </button>
                  )}
                </div>

                {visit.experts.length === 0 ? (
                  <div className="text-[11px] text-slate-400 italic bg-slate-50 p-2.5 rounded border">
                    No experts assigned yet to this committee.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                    {visit.experts.map((exp) => (
                      <div key={exp.id} className="p-2.5 bg-slate-50 rounded border text-xs space-y-0.5">
                        <div className="font-bold text-slate-900">{exp.expert_name}</div>
                        <div className="text-[11px] text-slate-600">{exp.designation}</div>
                        <div className="text-[10px] text-teal-800 truncate">{exp.organization}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{exp.contact_email}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions Footer */}
              {canManageEVC && (
                <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-end gap-2">
                  <button
                    onClick={() => setRescheduleModal({ open: true, visit })}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded shadow-sm transition-colors"
                  >
                    <Calendar className="w-3.5 h-3.5" /> Reschedule Visit
                  </button>

                  <button
                    onClick={() => setReportModal({ open: true, visit })}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm transition-colors"
                  >
                    <Upload className="w-3.5 h-3.5" /> Upload Inspection Report
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Reschedule Modal */}
      {rescheduleModal.open && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm sm:text-base border-b pb-2">
              Reschedule EVC Inspection Date
            </h3>
            <div className="text-xs text-slate-600">
              Application: <strong>{rescheduleModal.visit?.application_no}</strong>
            </div>

            <form onSubmit={handleRescheduleSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">New Inspection Date*</label>
                <input
                  type="date"
                  required
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  className="w-full text-xs p-1.5 border border-slate-300 rounded"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mandatory Delay Justification (Audit Invariant)*
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Specify official reason: e.g. expert roster conflict, regional weather warning, or institution formal deferral request..."
                  value={delayReason}
                  onChange={(e) => setDelayReason(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setRescheduleModal({ open: false, visit: null })}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded border"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={rescheduling || !delayReason.trim() || !newDate}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm disabled:opacity-50"
                >
                  {rescheduling ? 'Recording...' : 'Commit Reschedule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Expert Modal */}
      {expertModal.open && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm sm:text-base border-b pb-2">
              Assign Visiting Committee Expert
            </h3>

            <form onSubmit={handleExpertSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Expert Full Name*</label>
                <input
                  type="text"
                  required
                  placeholder="Prof. / Dr. Full Name"
                  value={expertName}
                  onChange={(e) => setExpertName(e.target.value)}
                  className="w-full text-xs p-1.5 border border-slate-300 rounded"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Designation & Department*</label>
                <input
                  type="text"
                  required
                  placeholder="Professor, Computer Science & Engg."
                  value={expertDesignation}
                  onChange={(e) => setExpertDesignation(e.target.value)}
                  className="w-full text-xs p-1.5 border border-slate-300 rounded"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Parent Institution / Organization*</label>
                <input
                  type="text"
                  required
                  placeholder="IIT / NIT / State Technical University"
                  value={expertOrg}
                  onChange={(e) => setExpertOrg(e.target.value)}
                  className="w-full text-xs p-1.5 border border-slate-300 rounded"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Official Contact Email*</label>
                <input
                  type="email"
                  required
                  placeholder="expert@university.edu.in"
                  value={expertEmail}
                  onChange={(e) => setExpertEmail(e.target.value)}
                  className="w-full text-xs p-1.5 border border-slate-300 rounded"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setExpertModal({ open: false, visit: null })}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded border"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={assigning || !expertName}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm disabled:opacity-50"
                >
                  {assigning ? 'Assigning...' : 'Confirm Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Inspection Report Modal */}
      {reportModal.open && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm sm:text-base border-b pb-2">
              Submit Official EVC Inspection Report
            </h3>

            <form onSubmit={handleReportSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Upload Signed EVC Report (PDF &le; 15MB)*
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf"
                  onChange={(e) => setReportFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-slate-600 border border-slate-300 rounded p-1.5 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Executive Inspection Summary & Compliance Findings*
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Summarize verification of physical land area, instructional labs, library holdings, faculty CAD, fire safety and barrier-free access..."
                  value={reportSummary}
                  onChange={(e) => setReportSummary(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setReportModal({ open: false, visit: null })}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded border"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReport || !reportFile || !reportSummary.trim()}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm disabled:opacity-50"
                >
                  {submittingReport ? 'Uploading & Hashing...' : 'Upload & Submit Report'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
