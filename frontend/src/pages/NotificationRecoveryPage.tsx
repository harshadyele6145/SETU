import React, { useState, useEffect } from 'react';
import { 
  Send, 
  RotateCcw, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Play, 
  Activity, 
  ServerCrash
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface NotificationItem {
  id: string;
  alert_id: string;
  alert_title: string | null;
  recipient_user_id: string | null;
  recipient_email: string;
  channel: string;
  status: string;
  retry_count: number;
  last_error: string | null;
  sent_at: string | null;
  created_at: string;
}

export const NotificationRecoveryPage: React.FC = () => {
  const { token } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Recovery simulation state
  const [simulatedDays, setSimulatedDays] = useState('30');
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [runningRecovery, setRunningRecovery] = useState(false);
  const [recoveryLog, setRecoveryLog] = useState<string | null>(null);

  const fetchNotifications = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/alerts/notifications', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setNotifications(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch notification outbox');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [token]);

  const handleRetry = async (notifId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`/api/alerts/notifications/${notifId}/retry`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await fetchNotifications();
    } catch (err: any) {
      alert(`Retry failed: ${err.message}`);
    }
  };

  const handleRunCatchup = async () => {
    if (!token) return;
    setRunningRecovery(true);
    setRecoveryLog(null);
    try {
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() + parseInt(simulatedDays, 10));

      const res = await fetch('/api/alerts/evaluate', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          fail_notifications: simulateFailure,
          simulated_date: targetDate.toISOString()
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRecoveryLog(
        `Catch-up complete for +${simulatedDays}d (${targetDate.toISOString().split('T')[0]}): ` +
        `${data.new_alerts_created} new alerts generated, ${data.duplicate_alerts_skipped} duplicates safely skipped via idempotency keys.`
      );
      await fetchNotifications();
    } catch (err: any) {
      alert(`Recovery simulation error: ${err.message}`);
    } finally {
      setRunningRecovery(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SENT':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'FAILED':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'RETRYING':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  const sentCount = notifications.filter((n) => n.status === 'SENT').length;
  const failedCount = notifications.filter((n) => n.status === 'FAILED').length;
  const retryingCount = notifications.filter((n) => n.status === 'RETRYING' || n.status === 'PENDING').length;

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Notification Outbox & Downtime Recovery
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Transactional outbox pattern, simulated email delivery, retry exhaustion, and scheduler downtime catch-up
          </p>
        </div>
      </div>

      {/* Simulator Card */}
      <div className="bg-navy-900 text-white p-5 rounded-lg border border-navy-700 shadow space-y-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-teal-400" />
          <h3 className="font-bold text-sm sm:text-base">Scheduler Downtime & Catch-Up Simulator</h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Simulate an environment where the background scheduler was offline or network delivery failed.
          When the evaluator executes, it catches up on all missed SLA windows and expirations without duplicating any previously generated alerts.
        </p>

        <div className="flex flex-wrap items-center gap-4 pt-2">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-300">Fast-forward time by:</span>
            <select
              value={simulatedDays}
              onChange={(e) => setSimulatedDays(e.target.value)}
              className="bg-navy-800 border border-navy-600 rounded px-2.5 py-1 text-teal-300 font-mono focus:outline-none"
            >
              <option value="0">Current Time (0 days)</option>
              <option value="7">+7 Days</option>
              <option value="15">+15 Days</option>
              <option value="30">+30 Days</option>
              <option value="60">+60 Days</option>
              <option value="90">+90 Days</option>
            </select>
          </div>

          <label className="flex items-center gap-2 text-xs cursor-pointer select-none">
            <input
              type="checkbox"
              checked={simulateFailure}
              onChange={(e) => setSimulateFailure(e.target.checked)}
              className="rounded text-teal-500 focus:ring-teal-400"
            />
            <span className="text-rose-300 flex items-center gap-1">
              <ServerCrash className="w-3.5 h-3.5" /> Simulate SMTP Outage (trigger retries)
            </span>
          </label>

          <button
            onClick={handleRunCatchup}
            disabled={runningRecovery}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-navy-900 bg-teal-400 hover:bg-teal-300 rounded shadow transition-colors disabled:opacity-50"
          >
            {runningRecovery ? (
              <RotateCcw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            <span>Execute Catch-Up</span>
          </button>
        </div>

        {recoveryLog && (
          <div className="p-3 bg-navy-800/80 border border-teal-500/40 rounded text-xs text-teal-200 font-mono">
            {recoveryLog}
          </div>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Delivered Notifications</div>
            <div className="text-2xl font-bold text-emerald-600">{sentCount}</div>
          </div>
          <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-full">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Queued / Retrying</div>
            <div className="text-2xl font-bold text-amber-600">{retryingCount}</div>
          </div>
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-full">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Failed (Retries Exhausted)</div>
            <div className="text-2xl font-bold text-rose-600">{failedCount}</div>
          </div>
          <div className="p-2.5 bg-rose-50 text-rose-600 rounded-full">
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Outbox Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="font-bold text-xs sm:text-sm text-slate-800 flex items-center gap-2">
            <Send className="w-4 h-4 text-teal-700" />
            Transactional Outbox Log (Recent Dispatches)
          </div>
          <button
            onClick={fetchNotifications}
            className="p-1 text-slate-500 hover:text-slate-800 rounded transition-colors"
            title="Refresh outbox log"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">
            Loading notification outbox records...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 bg-rose-50">
            Error: {error}
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No notification records in outbox. Run deadline evaluator to populate.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <th className="py-2.5 px-4">Alert Subject</th>
                  <th className="py-2.5 px-4">Recipient</th>
                  <th className="py-2.5 px-4">Channel</th>
                  <th className="py-2.5 px-4">Status & Attempts</th>
                  <th className="py-2.5 px-4">Delivery Timestamp / Error</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {notifications.map((n) => (
                  <tr key={n.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-4 max-w-xs truncate">
                      <div className="font-bold text-slate-900 truncate">{n.alert_title || 'System Alert'}</div>
                      <div className="text-[10px] text-slate-400 font-mono">Alert ID: {n.alert_id.substring(0, 8)}...</div>
                    </td>
                    <td className="py-2.5 px-4">
                      <div className="font-medium text-slate-800">{n.recipient_email}</div>
                    </td>
                    <td className="py-2.5 px-4">
                      <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded border">
                        {n.channel}
                      </span>
                    </td>
                    <td className="py-2.5 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(n.status)}`}>
                        {n.status}
                      </span>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        Retries: {n.retry_count} / 3
                      </div>
                    </td>
                    <td className="py-2.5 px-4 max-w-xs">
                      {n.sent_at ? (
                        <div className="text-slate-600">
                          {new Date(n.sent_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                        </div>
                      ) : n.last_error ? (
                        <div className="text-rose-600 text-[11px] truncate" title={n.last_error}>
                          {n.last_error}
                        </div>
                      ) : (
                        <div className="text-slate-400 italic">Pending dispatch</div>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      {(n.status === 'FAILED' || n.status === 'RETRYING') && (
                        <button
                          onClick={() => handleRetry(n.id)}
                          className="px-2 py-1 text-[11px] font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-300 rounded shadow-sm"
                        >
                          Retry Delivery
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
    </div>
  );
};
