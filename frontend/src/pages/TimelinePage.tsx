import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { 
  GitCommit, 
  ArrowLeft, 
  User
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

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
  history: HistoryItem[];
}

export const TimelinePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const appIdParam = searchParams.get('app_id');
  const { token } = useAuth();

  const [applications, setApplications] = useState<any[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string>(appIdParam || '');
  const [appDetail, setAppDetail] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch list of applications for selector
  useEffect(() => {
    if (!token) return;
    fetch('/api/applications', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((res) => res.json())
      .then((data) => {
        setApplications(data);
        if (!selectedAppId && data.length > 0) {
          setSelectedAppId(data[0].id);
        }
      })
      .catch(() => {});
  }, [token]);

  // Fetch detail for selected application
  useEffect(() => {
    if (!selectedAppId || !token) return;
    setLoading(true);
    setError(null);

    fetch(`/api/applications/${selectedAppId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setAppDetail(data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedAppId, token]);

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
              Application Timeline & Movement History
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Chronological audit of stage movements, committee observations, and institutional clarifications
            </p>
          </div>
        </div>

        {/* Application Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-600 font-medium">Select Case:</label>
          <select
            value={selectedAppId}
            onChange={(e) => setSelectedAppId(e.target.value)}
            className="text-xs sm:text-sm border border-slate-300 rounded px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500 max-w-[240px] truncate"
          >
            {applications.map((a) => (
              <option key={a.id} value={a.id}>
                {a.application_no} — {a.institution_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-lg border">
          Loading case timeline...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 rounded-lg border border-rose-200">
          Failed to load application timeline: {error}
        </div>
      ) : appDetail ? (
        <div className="space-y-6">
          {/* Case Summary Card */}
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-3 mb-4">
              <div>
                <span className="text-xs font-mono bg-slate-100 text-slate-700 px-2 py-0.5 rounded border">
                  {appDetail.route}
                </span>
                <h3 className="text-lg font-bold text-slate-900 font-mono mt-1">
                  {appDetail.application_no}
                </h3>
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
    </div>
  );
};
