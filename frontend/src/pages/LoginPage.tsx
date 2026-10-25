import React, { useState } from 'react';
import { 
  Lock, 
  Mail, 
  ShieldCheck, 
  AlertCircle, 
  KeyRound, 
  ChevronDown, 
  ChevronUp,
  Building2,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const EVALUATION_ACCOUNTS = [
  {
    role: 'RO_OFFICER',
    title: 'Regional Office Officer (North)',
    email: 'ro_north@aicte.gov.in',
    name: 'Dr. Arun Mehra',
    jurisdiction: 'Northern Regional Office (Kanpur)',
    badge: 'Regional Desk'
  },
  {
    role: 'INST_ADMIN',
    title: 'Institution Administrator',
    email: 'inst_admin@fictional-nist.edu.in',
    name: 'Dr. R. K. Verma',
    jurisdiction: 'National Inst of Science & Tech',
    badge: 'Institution'
  },
  {
    role: 'COMP_AUTH',
    title: 'Competent Authority (Council)',
    email: 'comp_auth@aicte.gov.in',
    name: 'Member Secretary (AICTE)',
    jurisdiction: 'Executive Committee (HQ)',
    badge: 'Sole Statutory Power'
  },
  {
    role: 'COMP_REV',
    title: 'Compliance Reviewer',
    email: 'compliance_reviewer@aicte.gov.in',
    name: 'Shri Vikramaditya Rao',
    jurisdiction: 'National Compliance Bureau',
    badge: 'Undertakings Review'
  },
  {
    role: 'EVC_COORD',
    title: 'EVC Coordinator',
    email: 'evc_coord@aicte.gov.in',
    name: 'Dr. Preeti Saxena',
    jurisdiction: 'Western Jurisdiction',
    badge: 'Inspection Visits'
  },
  {
    role: 'BUREAU_OFFICER',
    title: 'AICTE Bureau Officer',
    email: 'bureau_officer@aicte.gov.in',
    name: 'Dr. Meenakshi Sundaram',
    jurisdiction: 'AICTE HQ (New Delhi)',
    badge: 'National Scrutiny'
  }
];

export const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState<string>('ro_north@aicte.gov.in');
  const [password, setPassword] = useState<string>('DemoPass@2026');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showEvalAccounts, setShowEvalAccounts] = useState<boolean>(true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    const success = await login(email, password);
    if (!success) {
      setErrorMessage('Authentication failed. Incorrect email or password, or account is inactive.');
    }
  };

  const handleSelectAccount = (accountEmail: string) => {
    setEmail(accountEmail);
    setPassword('DemoPass@2026');
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen w-screen bg-slate-900 flex flex-col justify-between text-slate-100">
      {/* Top Subtle Branding Bar */}
      <header className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-950/60 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-teal-600 flex items-center justify-center font-bold text-white shadow-sm">
            S
          </div>
          <div>
            <span className="font-bold tracking-tight text-white text-sm sm:text-base">SETU</span>
            <span className="text-slate-400 text-xs ml-2 hidden sm:inline">AICTE Approval Operations Platform</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/80 px-3 py-1 rounded-full border border-slate-700/60 font-mono">
          <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
          <span>Server-Enforced RBAC</span>
        </div>
      </header>

      {/* Main Login Area */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-6 my-auto">
        <div className="w-full max-w-md space-y-6">
          {/* Card Header */}
          <div className="text-center space-y-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400 mb-1">
              <Building2 className="w-6 h-6" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Official Portal Sign-In
            </h1>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Unified Workflow, Compliance & Deadline Intelligence Platform for technical education approvals.
            </p>
          </div>

          {/* Form Card */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 sm:p-8 shadow-xl backdrop-blur-sm space-y-5">
            {errorMessage && (
              <div 
                role="alert"
                className="bg-rose-950/70 border border-rose-800/80 text-rose-200 text-xs p-3.5 rounded-lg flex items-start gap-2.5 animate-fadeIn"
              >
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div className="leading-relaxed">{errorMessage}</div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5" htmlFor="login-email">
                  Council Official / Institutional Work Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                  <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="officer@aicte.gov.in"
                    className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-900/90 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-300" htmlFor="login-password">
                    Account Password
                  </label>
                  <span className="text-[11px] text-teal-400 font-mono">DemoPass@2026</span>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                  <input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="••••••••••••"
                    className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-900/90 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-500 disabled:bg-teal-800 disabled:cursor-not-allowed text-white font-semibold text-xs rounded-lg shadow-md transition-all flex items-center justify-center gap-2 group mt-2"
              >
                {isLoading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                    <span>Authenticating Credentials...</span>
                  </>
                ) : (
                  <>
                    <span>Authenticate & Access Platform</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Prototype Evaluation Accounts Reference */}
          <div className="bg-slate-800/50 border border-slate-800 rounded-xl overflow-hidden text-xs">
            <button
              type="button"
              onClick={() => setShowEvalAccounts(!showEvalAccounts)}
              className="w-full px-4 py-2.5 flex items-center justify-between text-slate-400 hover:text-slate-200 transition-colors"
            >
              <span className="flex items-center gap-2 font-medium">
                <KeyRound className="w-3.5 h-3.5 text-teal-400" />
                <span>Prototype Test Accounts & Credentials (Evaluation Reference)</span>
              </span>
              {showEvalAccounts ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showEvalAccounts && (
              <div className="px-4 pb-4 pt-1 space-y-2 border-t border-slate-800/60">
                <p className="text-[11px] text-slate-400">
                  Clicking any persona below pre-fills the login form. Authorization and RBAC boundaries are strictly enforced on the server via JWT tokens:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                  {EVALUATION_ACCOUNTS.map((acc) => (
                    <button
                      key={acc.email}
                      type="button"
                      onClick={() => handleSelectAccount(acc.email)}
                      className={`text-left p-2.5 rounded-lg border transition-all ${
                        email === acc.email
                          ? 'border-teal-500/80 bg-teal-950/40 text-teal-200'
                          : 'border-slate-700/60 bg-slate-900/60 hover:border-slate-600 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="font-semibold text-[11px] text-white truncate">{acc.name}</span>
                        <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 bg-slate-800 text-teal-300 rounded border border-slate-700">
                          {acc.badge}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 truncate">{acc.jurisdiction}</div>
                      <div className="text-[10px] font-mono text-slate-500 truncate mt-0.5">{acc.email}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Discreet Truthful Footer */}
      <footer className="h-10 border-t border-slate-800 px-6 flex items-center justify-between text-[11px] text-slate-500 bg-slate-950/60">
        <span>SETU — AICTE Approval Operations Platform</span>
        <span>SETU Prototype · Sample Data · Fictional Regulatory Records for Evaluation</span>
      </footer>
    </div>
  );
};
