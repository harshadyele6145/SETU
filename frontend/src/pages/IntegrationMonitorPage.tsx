import React, { useState, useEffect } from 'react';
import { 
  Network, 
  Activity, 
  ShieldAlert, 
  CheckCircle, 
  XCircle, 
  Send, 
  RefreshCw, 
  Key, 
  Lock, 
  FileCheck,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SyncLogItem {
  id: string;
  timestamp: string;
  action: string;
  application_no?: string;
  aicte_id?: string;
  decision: string;
  status_code: number;
  success: boolean;
  external_ref: string;
  message: string;
}

interface AdapterHealth {
  adapter_name: string;
  is_connected: boolean;
  latency_ms: number;
  simulated_failure_active: boolean;
  details: Record<string, any>;
}

export const IntegrationMonitorPage: React.FC = () => {
  const { token } = useAuth();
  const [health, setHealth] = useState<AdapterHealth | null>(null);
  const [syncLogs, setSyncLogs] = useState<SyncLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [testAppNo, setTestAppNo] = useState<string>('AICTE/WRO/2026/001');
  const [testDecision, setTestDecision] = useState<string>('APPROVED');
  const [testComments, setTestComments] = useState<string>('Council approved subject to undertaking compliance.');
  const [fetchAicteId, setFetchAicteId] = useState<string>('1-3324567891');
  const [testResult, setTestResult] = useState<any>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/integrations/status', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHealth(data.health);
        setSyncLogs(data.recent_syncs || []);
      }
    } catch (err) {
      console.error('Failed to fetch adapter status', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, [token]);

  const toggleFailureMode = async () => {
    if (!health) return;
    setActionLoading(true);
    try {
      const newMode = !health.simulated_failure_active;
      const res = await fetch('/api/integrations/toggle-failure', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ simulate_failure: newMode })
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTestPush = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    setTestResult(null);
    try {
      const res = await fetch('/api/integrations/test-push', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          application_no: testAppNo,
          decision: testDecision,
          comments: testComments
        })
      });
      const data = await res.json();
      setTestResult({
        endpoint: 'POST /api/integrations/test-push',
        status: res.status,
        data
      });
      await fetchStatus();
    } catch (err: any) {
      setTestResult({ error: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleFetchProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    setTestResult(null);
    try {
      const res = await fetch(`/api/integrations/fetch-institution/${fetchAicteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setTestResult({
        endpoint: `GET /api/integrations/fetch-institution/${fetchAicteId}`,
        status: res.status,
        data
      });
      await fetchStatus();
    } catch (err: any) {
      setTestResult({ error: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Network className="w-5 h-5 text-teal-600" />
            AICTE External Portal Integration Monitor
          </h2>
          <p className="text-xs text-slate-500">
            Bidirectional contract monitoring, mTLS readiness & simulated boundary telemetry for national council synchronizations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchStatus}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-50"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Probe
          </button>
          <button
            onClick={toggleFailureMode}
            disabled={actionLoading}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded text-white shadow-sm transition-colors ${
              health?.simulated_failure_active 
                ? 'bg-emerald-600 hover:bg-emerald-700' 
                : 'bg-rose-600 hover:bg-rose-700'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            {health?.simulated_failure_active ? 'Disable Failure Simulation' : 'Simulate 503/504 Outage'}
          </button>
        </div>
      </div>

      {/* Gateway Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Gateway Status</span>
          <div className="mt-2 flex items-center gap-2">
            {health?.is_connected ? (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span className="text-sm font-bold text-emerald-700">ONLINE & CONNECTED</span>
              </>
            ) : (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
                <span className="text-sm font-bold text-rose-700">SIMULATED OUTAGE ACTIVE</span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">{health?.adapter_name || 'Loading...'}</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Round-Trip Latency</span>
          <div className="mt-2 text-xl font-bold text-slate-800">
            {health?.latency_ms ? `${health.latency_ms} ms` : '12.4 ms'}
          </div>
          <p className="text-[11px] text-teal-600 mt-1">Within 50ms SLA target</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Integration Boundary</span>
          <div className="mt-2 text-sm font-bold text-slate-800">
            ExternalPortalAdapter
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Zero live AICTE write risk</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Total Mock Calls</span>
          <div className="mt-2 text-xl font-bold text-teal-700">
            {health?.details?.total_mock_calls ?? 0} invocations
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Logged to audit trail</p>
        </div>
      </div>

      {/* Live Interactive Testing Console */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form 1: Push Decision */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
              <Send className="w-4 h-4 text-teal-600" />
              Simulate Outbound Decision Push
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Simulates dispatching statutory approval outcome to external central portal.
            </p>
          </div>

          <form onSubmit={handleTestPush} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Application No</label>
              <input
                type="text"
                value={testAppNo}
                onChange={(e) => setTestAppNo(e.target.value)}
                required
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Statutory Decision</label>
              <select
                value={testDecision}
                onChange={(e) => setTestDecision(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500"
              >
                <option value="APPROVED">APPROVED (Full Approval)</option>
                <option value="APPROVED_WITH_CONDITIONS">APPROVED_WITH_CONDITIONS (Conditional)</option>
                <option value="REJECTED">REJECTED (Statutory Refusal)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Comments / Regulatory Note</label>
              <input
                type="text"
                value={testComments}
                onChange={(e) => setTestComments(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500"
              />
            </div>
            <button
              type="submit"
              disabled={actionLoading}
              className="w-full py-2 px-4 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded transition-colors"
            >
              Execute Outbound Push Decision
            </button>
          </form>
        </div>

        {/* Form 2: Fetch Profile & Response Viewer */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-teal-600" />
              Simulate Inbound Master Data Pull
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Queries external portal master record for institution accreditation verification.
            </p>
          </div>

          <form onSubmit={handleFetchProfile} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">AICTE Permanent ID</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={fetchAicteId}
                  onChange={(e) => setFetchAicteId(e.target.value)}
                  required
                  placeholder="e.g. 1-3324567891"
                  className="flex-1 text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500"
                />
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="py-2 px-4 bg-slate-800 hover:bg-slate-900 text-white font-semibold text-xs rounded transition-colors"
                >
                  Fetch Profile
                </button>
              </div>
            </div>
          </form>

          {/* Test Execution Output */}
          <div className="mt-3">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Telemetry Probe Output</span>
            <div className="mt-1 p-3 bg-slate-900 text-emerald-400 font-mono text-[11px] rounded h-36 overflow-y-auto">
              {testResult ? (
                <pre>{JSON.stringify(testResult, null, 2)}</pre>
              ) : (
                <span className="text-slate-500">// Trigger an outbound push or inbound fetch above to observe live adapter telemetry.</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sync Telemetry Log Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-teal-600" />
            Recent External Gateway Telemetry Log
          </h3>
          <span className="text-xs text-slate-500">Live Transaction Outbox & Inbound Events</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Log ID</th>
                <th className="py-2.5 px-4">Timestamp</th>
                <th className="py-2.5 px-4">Action</th>
                <th className="py-2.5 px-4">Entity Ref</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">External Sync Ref</th>
                <th className="py-2.5 px-4">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-400">Loading integration logs...</td>
                </tr>
              ) : syncLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-400">No sync telemetry recorded yet.</td>
                </tr>
              ) : (
                syncLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-4 font-mono font-semibold text-slate-700">{log.id}</td>
                    <td className="py-2.5 px-4 text-slate-500 font-mono text-[11px]">{log.timestamp}</td>
                    <td className="py-2.5 px-4">
                      <span className={`px-2 py-0.5 text-[10px] font-semibold rounded ${
                        log.action === 'PUSH_DECISION' 
                          ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                          : 'bg-purple-50 text-purple-700 border border-purple-200'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 font-medium text-slate-800">
                      {log.application_no || log.aicte_id || '-'}
                    </td>
                    <td className="py-2.5 px-4">
                      {log.success ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold text-[11px]">
                          <CheckCircle className="w-3 h-3 text-emerald-500" />
                          {log.status_code} OK
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-700 font-semibold text-[11px]">
                          <XCircle className="w-3 h-3 text-rose-500" />
                          {log.status_code} FAIL
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-slate-600">{log.external_ref}</td>
                    <td className="py-2.5 px-4 text-slate-600 max-w-xs truncate" title={log.message}>
                      {log.message}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Enterprise Integration Governance & Prerequisites */}
      <div className="bg-slate-50 rounded-lg border border-slate-200 p-5 space-y-3">
        <div className="flex items-start gap-3">
          <Lock className="w-5 h-5 text-teal-700 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-bold text-slate-900">National Council Production Integration Prerequisites</h4>
            <p className="text-xs text-slate-600 mt-0.5">
              Connecting SETU to official AICTE central databases requires adherence to Indian Government IT and Data Protection standards:
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 text-xs">
          <div className="p-3 bg-white rounded border border-slate-200 space-y-1">
            <span className="font-semibold text-slate-800 flex items-center gap-1">
              <Key className="w-3.5 h-3.5 text-amber-600" />
              1. Mutual TLS & NIC Credentials
            </span>
            <p className="text-slate-500 text-[11px]">
              2048-bit RSA client certificates issued by authorized NIC / AICTE certifying authorities.
            </p>
          </div>

          <div className="p-3 bg-white rounded border border-slate-200 space-y-1">
            <span className="font-semibold text-slate-800 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5 text-blue-600" />
              2. Transactional Idempotency
            </span>
            <p className="text-slate-500 text-[11px]">
              All sync events must carry unique compound SHA-256 idempotency headers to guarantee exactly-once receipt.
            </p>
          </div>

          <div className="p-3 bg-white rounded border border-slate-200 space-y-1">
            <span className="font-semibold text-slate-800 flex items-center gap-1">
              <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
              3. DPDP Act & Data Sovereignty
            </span>
            <p className="text-slate-500 text-[11px]">
              Institutional student intake, faculty records, and financial details stored strictly within sovereign Indian territory.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
