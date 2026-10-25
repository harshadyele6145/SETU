import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Search, 
  Filter, 
  Play, 
  Flame, 
  Building2, 
  RotateCcw
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface AlertItem {
  id: string;
  entity_type: string;
  entity_id: string;
  institution_id: string | null;
  institution_name: string | null;
  region_id: string | null;
  region_name: string | null;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  idempotency_key: string;
  is_acknowledged: boolean;
  acknowledged_by_id: string | null;
  acknowledged_by_name: string | null;
  acknowledged_at: string | null;
  is_escalated: boolean;
  escalation_level: number;
  created_at: string;
}

interface EvaluationResult {
  total_candidates_evaluated: number;
  new_alerts_created: number;
  duplicate_alerts_skipped: number;
  notifications_enqueued: number;
  dispatch_summary: {
    processed: number;
    sent: number;
    failed: number;
    retrying: number;
  };
}

export const AlertsPage: React.FC = () => {
  const { token } = useAuth();
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [ackFilter, setAckFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');

  // Evaluator status
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<EvaluationResult | null>(null);

  const fetchAlerts = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      let url = '/api/alerts?';
      if (severityFilter) url += `severity=${encodeURIComponent(severityFilter)}&`;
      if (ackFilter !== '') url += `is_acknowledged=${ackFilter}&`;
      if (entityFilter) url += `entity_type=${encodeURIComponent(entityFilter)}&`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAlerts(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [token, severityFilter, ackFilter, entityFilter]);

  const handleAcknowledge = async (alertId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`/api/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to acknowledge');
      }
      await fetchAlerts();
    } catch (err: any) {
      alert(`Acknowledgment error: ${err.message}`);
    }
  };

  const triggerEvaluation = async () => {
    if (!token) return;
    setEvaluating(true);
    setEvalResult(null);
    try {
      const res = await fetch('/api/alerts/evaluate', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ fail_notifications: false })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setEvalResult(data);
      await fetchAlerts();
    } catch (err: any) {
      alert(`Evaluation error: ${err.message}`);
    } finally {
      setEvaluating(false);
    }
  };

  const filtered = alerts.filter((a) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      a.title.toLowerCase().includes(q) ||
      a.message.toLowerCase().includes(q) ||
      (a.institution_name && a.institution_name.toLowerCase().includes(q)) ||
      a.idempotency_key.toLowerCase().includes(q)
    );
  });

  // Calculate metrics
  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL').length;
  const highCount = alerts.filter((a) => a.severity === 'HIGH').length;
  const unackCount = alerts.filter((a) => !a.is_acknowledged).length;
  const escalatedCount = alerts.filter((a) => a.is_escalated).length;

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-rose-50 text-rose-700 border-rose-300 ring-rose-200';
      case 'HIGH':
        return 'bg-amber-50 text-amber-700 border-amber-300 ring-amber-200';
      case 'MEDIUM':
        return 'bg-blue-50 text-blue-700 border-blue-300 ring-blue-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-300 ring-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Trigger Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Deadline Intelligence & Multi-Tier Alerts
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Idempotent SLA monitoring, compliance due-date tracking, escalation levels, and audit trail
          </p>
        </div>

        <button
          onClick={triggerEvaluation}
          disabled={evaluating}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-navy-800 hover:bg-navy-900 text-white text-xs sm:text-sm font-semibold rounded shadow transition-colors disabled:opacity-50"
        >
          {evaluating ? (
            <RotateCcw className="w-4 h-4 animate-spin text-teal-400" />
          ) : (
            <Play className="w-4 h-4 text-teal-400 fill-teal-400" />
          )}
          <span>{evaluating ? 'Evaluating Deadlines...' : 'Run Evaluator (Idempotent)'}</span>
        </button>
      </div>

      {/* Evaluator Output Banner */}
      {evalResult && (
        <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg text-xs space-y-1 text-teal-900">
          <div className="font-bold flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-teal-600" />
            Evaluation Completed Across Active Dataset
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
            <div>Candidates Evaluated: <strong>{evalResult.total_candidates_evaluated}</strong></div>
            <div>New Alerts Generated: <strong className="text-emerald-700">{evalResult.new_alerts_created}</strong></div>
            <div>Duplicates Skipped: <strong className="text-blue-700">{evalResult.duplicate_alerts_skipped}</strong></div>
            <div>Notifications Dispatched: <strong>{evalResult.dispatch_summary.sent}</strong></div>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Critical Breaches</div>
            <div className="text-2xl font-bold text-rose-600">{criticalCount}</div>
          </div>
          <div className="p-2.5 bg-rose-50 text-rose-600 rounded-full">
            <Flame className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">High Priority (&le;24h)</div>
            <div className="text-2xl font-bold text-amber-600">{highCount}</div>
          </div>
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-full">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Pending Ack</div>
            <div className="text-2xl font-bold text-teal-700">{unackCount}</div>
          </div>
          <div className="p-2.5 bg-teal-50 text-teal-700 rounded-full">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500">Escalated to RO/HQ</div>
            <div className="text-2xl font-bold text-purple-700">{escalatedCount}</div>
          </div>
          <div className="p-2.5 bg-purple-50 text-purple-700 rounded-full">
            <Building2 className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search alerts or institutions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs sm:text-sm border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={ackFilter}
            onChange={(e) => setAckFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All States</option>
            <option value="false">Pending Acknowledgment</option>
            <option value="true">Acknowledged</option>
          </select>

          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
          >
            <option value="">All Domain Entities</option>
            <option value="APPLICATION">Applications (SLA)</option>
            <option value="COMPLIANCE">Compliance Obligations</option>
            <option value="DOCUMENT">Document Expirations</option>
          </select>
        </div>
      </div>

      {/* Alert Feed */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border">
          Loading active alert stream...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 rounded-lg border border-rose-200">
          Error: {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border space-y-2">
          <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto" />
          <div>No active alerts matching the selected criteria.</div>
          <button 
            onClick={triggerEvaluation}
            className="text-teal-600 underline font-medium hover:text-teal-800"
          >
            Run an evaluation to scan active deadlines
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-lg border bg-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all ${
                alert.is_acknowledged ? 'opacity-70 bg-slate-50/70' : ''
              }`}
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-bold border uppercase ${getSeverityStyle(alert.severity)}`}>
                    {alert.severity}
                  </span>

                  <span className="text-[10px] font-mono px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded border">
                    {alert.entity_type}
                  </span>

                  {alert.is_escalated && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-100 text-purple-800 border border-purple-300">
                      Level {alert.escalation_level} Escalated
                    </span>
                  )}

                  <span className="text-[11px] text-slate-400">
                    {new Date(alert.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                  </span>
                </div>

                <h3 className="font-bold text-slate-900 text-sm">{alert.title}</h3>
                <p className="text-xs text-slate-600">{alert.message}</p>

                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500 pt-1">
                  {alert.institution_name && (
                    <div>Institution: <strong className="text-teal-800">{alert.institution_name}</strong></div>
                  )}
                  {alert.region_name && (
                    <div>Region: <strong>{alert.region_name}</strong></div>
                  )}
                  <div className="font-mono text-[10px] text-slate-400">Key: {alert.idempotency_key}</div>
                </div>
              </div>

              {/* Action */}
              <div className="shrink-0 text-right">
                {alert.is_acknowledged ? (
                  <div className="text-right">
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-300 px-2.5 py-1 rounded">
                      <CheckCircle className="w-3.5 h-3.5" /> Acknowledged
                    </span>
                    <div className="text-[10px] text-slate-400 mt-1">
                      by {alert.acknowledged_by_name || 'Officer'}
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    className="w-full md:w-auto px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded shadow-sm transition-colors"
                  >
                    Acknowledge Alert
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
