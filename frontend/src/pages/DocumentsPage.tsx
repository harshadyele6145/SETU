import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Download
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface DocumentItem {
  id: string;
  institution_name: string;
  document_category: string;
  title: string;
  issue_date: string;
  expiry_date: string;
  current_version: number;
  status: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  sha256_hash: string;
  verified_by_name: string | null;
  previous_document_id: string | null;
  days_to_expiry: number;
}

export const DocumentsPage: React.FC = () => {
  const { user, token } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Renewal Modal
  const [renewModal, setRenewModal] = useState<{ open: boolean; document: DocumentItem | null }>({
    open: false,
    document: null
  });
  const [renewFile, setRenewFile] = useState<File | null>(null);
  const [newIssueDate, setNewIssueDate] = useState('');
  const [newExpiryDate, setNewExpiryDate] = useState('');
  const [renewing, setRenewing] = useState(false);

  const fetchDocuments = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      let url = '/api/documents?';
      if (categoryFilter) url += `category=${encodeURIComponent(categoryFilter)}&`;
      if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}&`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load document registry');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [token, categoryFilter, statusFilter]);

  const handleRenewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renewModal.document || !renewFile || !newExpiryDate || !token) return;
    setRenewing(true);

    try {
      const formData = new FormData();
      formData.append('file', renewFile);
      formData.append('issue_date', newIssueDate || new Date().toISOString().split('T')[0]);
      formData.append('expiry_date', newExpiryDate);

      const res = await fetch(`/api/documents/${renewModal.document.id}/renew`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Renewal submission failed');
      }

      setRenewModal({ open: false, document: null });
      setRenewFile(null);
      setNewIssueDate('');
      setNewExpiryDate('');
      await fetchDocuments();
    } catch (err: any) {
      alert(`Renewal error: ${err.message}`);
    } finally {
      setRenewing(false);
    }
  };

  const handleVerify = async (docId: string, isVerified: boolean) => {
    if (!token) return;
    try {
      const res = await fetch(`/api/documents/${docId}/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          is_verified: isVerified,
          comments: isVerified ? 'Verified renewal document against registration norms.' : 'Deficient renewal.'
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Verification failed');
      }
      await fetchDocuments();
    } catch (err: any) {
      alert(`Verification error: ${err.message}`);
    }
  };

  const downloadDocument = async (docId: string, title: string) => {
    if (!token) return;
    try {
      const res = await fetch(`/api/documents/${docId}/download`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Download rejected');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`Protected download error: ${err.message}`);
    }
  };

  const filtered = documents.filter((doc) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      doc.title.toLowerCase().includes(q) ||
      doc.institution_name.toLowerCase().includes(q) ||
      doc.document_category.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VALID':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'EXPIRED':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'EXPIRING_SOON':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'RENEWAL_SUBMITTED':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'SUPERSEDED':
        return 'bg-slate-100 text-slate-500 border-slate-200 line-through';
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
            Prescribed Documents & Lease Validity Registry
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Monitoring registered lease validity, municipal approvals, replacement renewals, and version linkage
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by title or institution..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs sm:text-sm border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Categories</option>
            <option value="LEASE_DEED">Registered Lease Deed</option>
            <option value="FIRE_NOC">Municipal Fire NOC</option>
            <option value="BUILDING_SAFETY">Building Safety Certificate</option>
            <option value="OCCUPANCY_CERT">Occupancy Certificate</option>
            <option value="AICTE_AFFIDAVIT">AICTE Affidavit</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Validity States</option>
            <option value="VALID">Valid</option>
            <option value="EXPIRING_SOON">Expiring Soon (&le; 90 days)</option>
            <option value="EXPIRED">Expired</option>
            <option value="RENEWAL_SUBMITTED">Renewal Submitted</option>
            <option value="SUPERSEDED">Superseded Versions</option>
          </select>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">
            Loading document validity records...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 bg-rose-50">
            Error: {error}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No document records match your query.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs sm:text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold text-xs">
                  <th className="py-3 px-4">Document Title & Category</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Validity Window</th>
                  <th className="py-3 px-4">Status & Countdown</th>
                  <th className="py-3 px-4">Version & Checksum</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{doc.title}</div>
                      <div className="text-[11px] font-mono text-teal-700">{doc.document_category}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-700">
                      <div className="font-medium">{doc.institution_name}</div>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-600">
                      <div>Issued: {doc.issue_date}</div>
                      <div>Expiry: <strong>{doc.expiry_date}</strong></div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${getStatusBadge(doc.status)}`}>
                        {doc.status.replace(/_/g, ' ')}
                      </span>
                      <div className="text-[11px] mt-0.5">
                        {doc.days_to_expiry < 0 ? (
                          <span className="text-rose-600 font-bold">{Math.abs(doc.days_to_expiry)} days overdue</span>
                        ) : doc.days_to_expiry <= 90 ? (
                          <span className="text-amber-600 font-semibold">{doc.days_to_expiry} days to expiry</span>
                        ) : (
                          <span className="text-slate-500">{doc.days_to_expiry} days valid</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-xs font-mono">
                      <div>Version {doc.current_version} {doc.previous_document_id && <span className="text-slate-400">(renewed)</span>}</div>
                      <div className="text-[10px] text-slate-400 truncate max-w-[150px]" title={doc.sha256_hash}>
                        SHA: {doc.sha256_hash.substring(0, 10)}...
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                      {/* Protected Download Button */}
                      <button
                        onClick={() => downloadDocument(doc.id, doc.title)}
                        className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded border border-slate-300 transition-colors"
                        title="Download Protected Document"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>

                      {/* Institution Submit Renewal Button */}
                      {user?.role === 'INST_ADMIN' && doc.status !== 'SUPERSEDED' && (
                        <button
                          onClick={() => setRenewModal({ open: true, document: doc })}
                          className="px-2.5 py-1 text-xs font-medium text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-300 rounded shadow-sm"
                        >
                          Submit Renewal
                        </button>
                      )}

                      {/* Officer Verify Renewal Button */}
                      {['RO_OFFICER', 'REGIONAL_DIR', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_REVIEW', 'COMP_REV', 'COMP_AUTH', 'SYS_ADMIN'].includes(user?.role || '') &&
                        doc.status === 'RENEWAL_SUBMITTED' && (
                          <button
                            onClick={() => handleVerify(doc.id, true)}
                            className="px-2.5 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 rounded shadow-sm"
                          >
                            Verify Renewal
                          </button>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Renewal Upload Modal */}
      {renewModal.open && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm sm:text-base border-b pb-2">
              Submit Replacement Document for Renewal
            </h3>
            <div className="text-xs text-slate-600">
              <p>Document: <strong>{renewModal.document?.title}</strong></p>
              <p>Current Version: <strong>v{renewModal.document?.current_version}</strong> &rarr; New: <strong>v{(renewModal.document?.current_version || 1) + 1}</strong></p>
            </div>

            <form onSubmit={handleRenewSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Upload Replacement Certificate/Deed (PDF, DOCX &le; 15MB)*
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.png"
                  onChange={(e) => setRenewFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-slate-600 border border-slate-300 rounded p-1.5 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">New Issue Date*</label>
                  <input
                    type="date"
                    required
                    value={newIssueDate}
                    onChange={(e) => setNewIssueDate(e.target.value)}
                    className="w-full text-xs p-1.5 border border-slate-300 rounded"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">New Expiry Date*</label>
                  <input
                    type="date"
                    required
                    value={newExpiryDate}
                    onChange={(e) => setNewExpiryDate(e.target.value)}
                    className="w-full text-xs p-1.5 border border-slate-300 rounded"
                  />
                </div>
              </div>

              <div className="text-[11px] bg-amber-50 border border-amber-200 rounded p-2 text-amber-800">
                Notice: Uploaded replacement enters <strong>RENEWAL_SUBMITTED</strong>. The prior document enters <strong>SUPERSEDED</strong>. Verification by an authorized officer is required before the renewed document is recognized as VALID.
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setRenewModal({ open: false, document: null })}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded border border-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={renewing || !renewFile}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm disabled:opacity-50"
                >
                  {renewing ? 'Hashing & Saving...' : 'Submit Replacement Renewal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

