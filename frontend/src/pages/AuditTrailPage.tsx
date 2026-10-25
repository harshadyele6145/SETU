import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  RefreshCw, 
  CheckCircle2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface AuditItem {
  id: string;
  sequence_no: number;
  timestamp: string;
  actor_id: string | null;
  actor_role: string;
  action: string;
  entity_type: string;
  entity_id: string;
  previous_state: string | null;
  new_state: string | null;
  details_json: string;
  previous_hash: string;
  current_hash: string;
}

interface VerificationResult {
  is_valid: boolean;
  total_events_checked: number;
  genesis_hash_valid: boolean;
  broken_sequence_no: number | null;
  verification_message: string;
  checked_at: string;
}

export const AuditTrailPage: React.FC = () => {
  const { token } = useAuth();
  const [events, setEvents] = useState<AuditItem[]>([]);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAuditEvents = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/audit?limit=100', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setEvents(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit events');
    } finally {
      setLoading(false);
    }
  };

  const runVerification = async () => {
    if (!token) return;
    setVerifying(true);
    try {
      const res = await fetch('/api/audit/verify-chain', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setVerification(data);
    } catch (err: any) {
      alert(`Verification error: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    fetchAuditEvents();
    runVerification();
  }, [token]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Immutable Audit Trail & Cryptographic Verification
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Append-only tamper-evident ledger secured with sequential SHA-256 hash chaining
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={runVerification}
            disabled={verifying}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm disabled:opacity-50 transition-colors"
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
            {verifying ? 'Verifying Chain...' : 'Verify Cryptographic Hash Chain'}
          </button>
          <button
            onClick={fetchAuditEvents}
            className="p-1.5 text-slate-600 hover:bg-white rounded border border-slate-300"
            title="Refresh Ledger"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Verification Status Banner */}
      {verification && (
        <div
          className={`p-4 rounded-lg border flex items-start gap-3 shadow-sm ${
            verification.is_valid
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-rose-50 border-rose-200 text-rose-900'
          }`}
        >
          {verification.is_valid ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          )}
          <div className="text-xs sm:text-sm">
            <div className="font-bold">
              {verification.is_valid ? 'Cryptographic Hash Chain Intact' : 'CRITICAL: Audit Log Alteration Detected!'}
            </div>
            <p className="text-xs opacity-90 mt-0.5">
              {verification.verification_message} Checked{' '}
              <strong>{verification.total_events_checked}</strong> consecutive audit events.
            </p>
            <div className="text-[11px] opacity-75 mt-1 font-mono">
              Last Verified: {new Date(verification.checked_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
            </div>
          </div>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-xs sm:text-sm text-slate-800">
            Recorded Administrative & Statutory Events ({events.length})
          </h3>
          <span className="text-[11px] text-slate-400 font-mono">
            Genesis Hash: 0000000000000000000000000000000000000000000000000000000000000000
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">
            Loading append-only cryptographic ledger...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 bg-rose-50">
            Error: {error}
          </div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No audit events found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <th className="py-2.5 px-3">Seq #</th>
                  <th className="py-2.5 px-3">Timestamp (IST)</th>
                  <th className="py-2.5 px-3">Actor & Role</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3">Entity Reference</th>
                  <th className="py-2.5 px-3">Previous Hash &rarr; Current Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {events.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-teal-700">
                      #{evt.sequence_no}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 whitespace-nowrap">
                      {new Date(evt.timestamp).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                    </td>
                    <td className="py-2.5 px-3 text-slate-800 font-sans">
                      <span className="font-semibold">{evt.actor_role}</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-900 font-sans font-medium">
                      {evt.action}
                      {evt.previous_state && evt.new_state && (
                        <div className="text-[10px] text-slate-400 font-mono">
                          {evt.previous_state} &rarr; {evt.new_state}
                        </div>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                      {evt.entity_type}:{evt.entity_id.substring(0, 8)}...
                    </td>
                    <td className="py-2.5 px-3 text-[10px]">
                      <div className="text-slate-400 truncate max-w-[200px]" title={evt.previous_hash}>
                        Prev: {evt.previous_hash.substring(0, 16)}...
                      </div>
                      <div className="text-teal-700 font-semibold truncate max-w-[200px]" title={evt.current_hash}>
                        Curr: {evt.current_hash.substring(0, 16)}...
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
