import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  Clock, 
  Filter, 
  Search
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface EvidenceItem {
  id: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  sha256_hash: string;
  notes: string | null;
  submitted_by_name: string | null;
  submission_date: string;
  verification_status: string;
  verified_by_name: string | null;
  verified_at: string | null;
  rejection_reason: string | null;
}

interface ObligationItem {
  id: string;
  application_no: string | null;
  institution_name: string;
  category: string;
  title: string;
  description: string;
  condition_source: string;
  due_date: string;
  status: string;
  responsible_person: string | null;
  reviewer_name: string | null;
  review_comments: string | null;
  days_remaining: number;
  evidences: EvidenceItem[];
}

export const CompliancePage: React.FC = () => {
  const { user, token } = useAuth();
  const [obligations, setObligations] = useState<ObligationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [uploadModal, setUploadModal] = useState<{ open: boolean; obligation: ObligationItem | null }>({
    open: false,
    obligation: null
  });
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadNotes, setUploadNotes] = useState('');
  const [uploading, setUploading] = useState(false);

  const [verifyModal, setVerifyModal] = useState<{
    open: boolean;
    evidence: EvidenceItem | null;
    obligation: ObligationItem | null;
  }>({ open: false, evidence: null, obligation: null });
  const [isApproved, setIsApproved] = useState(true);
  const [verifyComments, setVerifyComments] = useState('');
  const [verifying, setVerifying] = useState(false);

  const fetchObligations = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      let url = '/api/compliance/obligations?';
      if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}&`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setObligations(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load compliance obligations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObligations();
  }, [token, statusFilter]);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadModal.obligation || !uploadFile || !token) return;
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      if (uploadNotes) formData.append('notes', uploadNotes);

      const res = await fetch(`/api/compliance/obligations/${uploadModal.obligation.id}/evidence`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      setUploadModal({ open: false, obligation: null });
      setUploadFile(null);
      setUploadNotes('');
      await fetchObligations();
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifyModal.evidence || !token) return;
    setVerifying(true);

    try {
      const res = await fetch(`/api/compliance/evidence/${verifyModal.evidence.id}/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          is_approved: isApproved,
          review_comments: verifyComments
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Verification action failed');
      }

      setVerifyModal({ open: false, evidence: null, obligation: null });
      setVerifyComments('');
      await fetchObligations();
    } catch (err: any) {
      alert(`Verification error: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  const filtered = obligations.filter((ob) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      ob.title.toLowerCase().includes(q) ||
      ob.institution_name.toLowerCase().includes(q) ||
      ob.category.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
      case 'CLOSED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'OVERDUE':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'DEFICIENT':
        return 'bg-red-50 text-red-700 border-red-300';
      case 'DUE_SOON':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'SUBMITTED':
      case 'UNDER_VERIFICATION':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Undertakings & Institutional Compliance
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Digital tracking of approval conditions precedent, evidence submission, and formal verification
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by condition or institution..."
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
            <option value="">All Statuses</option>
            <option value="UPCOMING">Upcoming</option>
            <option value="DUE_SOON">Due Soon (&le; 7 days)</option>
            <option value="SUBMITTED">Submitted (Pending Verification)</option>
            <option value="VERIFIED">Verified</option>
            <option value="DEFICIENT">Deficient / Rejected</option>
            <option value="OVERDUE">Overdue</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
      </div>

      {/* Obligations Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border">
          Loading institutional compliance obligations...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 rounded-lg border border-rose-200">
          Error: {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-8 text-center text-xs text-slate-500 bg-white rounded-lg border">
          No compliance obligations match your query.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((ob) => (
            <div key={ob.id} className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3 flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <span className="text-[10px] font-mono uppercase bg-slate-100 text-slate-600 px-2 py-0.5 rounded border">
                    {ob.category}
                  </span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${getStatusBadge(ob.status)}`}>
                    {ob.status}
                  </span>
                </div>

                <h3 className="font-bold text-slate-900 text-sm">{ob.title}</h3>
                <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{ob.description}</p>
                <div className="text-[11px] text-teal-800 font-medium mt-1">
                  Institution: <strong>{ob.institution_name}</strong>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-100 text-xs">
                <div className="flex items-center justify-between text-slate-600">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    Due Date: <strong>{ob.due_date}</strong>
                  </span>
                  <span className={ob.days_remaining < 0 ? 'text-rose-600 font-bold' : ob.days_remaining <= 7 ? 'text-amber-600 font-semibold' : 'text-slate-500'}>
                    {ob.days_remaining < 0 ? `${Math.abs(ob.days_remaining)}d overdue` : `${ob.days_remaining}d remaining`}
                  </span>
                </div>

                {ob.review_comments && (
                  <div className="p-2 bg-slate-50 rounded border border-slate-200 text-[11px] text-slate-700 italic">
                    Reviewer Notes: "{ob.review_comments}"
                  </div>
                )}

                {/* Evidence items submitted */}
                {ob.evidences && ob.evidences.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <div className="text-[11px] font-semibold text-slate-700">Submitted Proofs ({ob.evidences.length}):</div>
                    {ob.evidences.map((ev) => (
                      <div key={ev.id} className="p-2 bg-slate-50 rounded border flex items-center justify-between">
                        <div className="truncate max-w-[200px]">
                          <div className="font-medium text-slate-800 truncate">{ev.file_name}</div>
                          <div className="text-[10px] text-slate-400 font-mono">SHA: {ev.sha256_hash.substring(0, 12)}...</div>
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${getStatusBadge(ev.verification_status)}`}>
                            {ev.verification_status}
                          </span>
                          {/* Review button for authorized roles */}
                          {['COMP_REVIEW', 'COMP_REV', 'RO_OFFICER', 'REGIONAL_DIR', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH', 'SYS_ADMIN'].includes(user?.role || '') &&
                            ev.verification_status === 'SUBMITTED' && (
                              <button
                                onClick={() => setVerifyModal({ open: true, evidence: ev, obligation: ob })}
                                className="px-2 py-0.5 text-[11px] bg-teal-600 hover:bg-teal-700 text-white font-medium rounded shadow-sm"
                              >
                                Review
                              </button>
                            )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Institution submit evidence button */}
                {user?.role === 'INST_ADMIN' && ob.status !== 'VERIFIED' && ob.status !== 'CLOSED' && (
                  <button
                    onClick={() => setUploadModal({ open: true, obligation: ob })}
                    className="w-full mt-2 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-300 rounded shadow-sm transition-colors"
                  >
                    <Upload className="w-3.5 h-3.5" /> Submit Evidence Document
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Submit Evidence Modal */}
      {uploadModal.open && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm sm:text-base border-b pb-2">
              Submit Compliance Evidence (INV-01)
            </h3>
            <p className="text-xs text-slate-600">
              Obligation: <strong>{uploadModal.obligation?.title}</strong>
            </p>

            <form onSubmit={handleUploadSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Select Document File (PDF, DOCX, PNG &le; 15MB)*
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.png,.jpg,.jpeg,.docx"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-slate-600 border border-slate-300 rounded p-1.5 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Institutional Submission Remarks
                </label>
                <textarea
                  rows={2}
                  placeholder="Details of vendor, installation certificate, or compliance notes..."
                  value={uploadNotes}
                  onChange={(e) => setUploadNotes(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              <div className="text-[11px] bg-amber-50 border border-amber-200 rounded p-2 text-amber-800">
                Notice: Uploaded proof enters state <strong>SUBMITTED</strong>. Regulatory verification requires review by an authorized AICTE compliance officer.
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setUploadModal({ open: false, obligation: null })}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded border border-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm disabled:opacity-50"
                >
                  {uploading ? 'Uploading & Hashing...' : 'Upload & Submit Evidence'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Verify Evidence Modal */}
      {verifyModal.open && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm sm:text-base border-b pb-2">
              Official Compliance Verification
            </h3>
            <div className="text-xs text-slate-600">
              <p>File: <strong className="font-mono">{verifyModal.evidence?.file_name}</strong></p>
              <p>SHA-256: <span className="font-mono text-[10px] text-slate-500">{verifyModal.evidence?.sha256_hash}</span></p>
            </div>

            <form onSubmit={handleVerifySubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Verification Determination*</label>
                <div className="flex items-center gap-4 text-xs">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      checked={isApproved === true}
                      onChange={() => setIsApproved(true)}
                    />
                    <span className="text-emerald-700 font-semibold">Verify & Accept Proof</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      checked={isApproved === false}
                      onChange={() => setIsApproved(false)}
                    />
                    <span className="text-rose-700 font-semibold">Reject as Deficient</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Reviewer Rationale & Audit Findings (Mandatory)*
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder={isApproved ? "Confirm validity and conformance with handbook..." : "Specify exact reason for deficiency..."}
                  value={verifyComments}
                  onChange={(e) => setVerifyComments(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setVerifyModal({ open: false, evidence: null, obligation: null })}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded border border-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={verifying || !verifyComments.trim()}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm disabled:opacity-50"
                >
                  {verifying ? 'Recording...' : 'Commit Determination'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

