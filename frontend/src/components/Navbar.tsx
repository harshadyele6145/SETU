import React, { useState, useEffect } from 'react';
import { User, LogOut, CheckCircle2, AlertCircle, ChevronDown, Shield, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/health');
        if (res.ok) {
          const data = await res.json();
          setBackendHealthy(data.database_connected === true);
        } else {
          setBackendHealthy(false);
        }
      } catch (err) {
        setBackendHealthy(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between shrink-0 shadow-sm relative z-30">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800 text-sm sm:text-base hidden sm:inline">
            SETU — AICTE Approval Operations Platform
          </span>
          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-300 font-mono">
            Enterprise Console
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 sm:gap-4">
        {/* Backend health indicator */}
        <div 
          className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border border-slate-200 bg-slate-50"
          title={backendHealthy ? "Backend API & PostgreSQL/SQLite connected" : "Backend unreachable"}
        >
          {backendHealthy === true ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-emerald-700 font-medium hidden md:inline">API Connected</span>
            </>
          ) : backendHealthy === false ? (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
              <span className="text-rose-700 font-medium hidden md:inline">API Degraded</span>
            </>
          ) : (
            <span className="text-slate-500 font-medium">Checking...</span>
          )}
        </div>

        {/* Authenticated User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 text-xs sm:text-sm bg-slate-50 hover:bg-slate-100 px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-700 transition-colors"
            title="User Profile & Session Details"
            aria-expanded={dropdownOpen}
          >
            <div className="w-6 h-6 rounded-full bg-teal-600 flex items-center justify-center text-white text-xs font-semibold">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="text-left hidden sm:block">
              <div className="font-semibold text-slate-900 leading-tight truncate max-w-[160px]">
                {user?.full_name || 'Authenticated Official'}
              </div>
              <div className="text-[10px] text-teal-700 font-mono font-medium">
                {user?.role || 'User'}
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 animate-fadeIn">
              <div className="px-4 py-2 border-b border-slate-100">
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Signed in as
                </div>
                <div className="font-semibold text-xs text-slate-900 mt-0.5 truncate">
                  {user?.full_name}
                </div>
                <div className="text-[11px] text-slate-500 font-mono truncate">
                  {user?.email}
                </div>
                <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-50 text-teal-800 border border-teal-200">
                  <Shield className="w-3 h-3 text-teal-600" />
                  <span>Role: {user?.role}</span>
                </div>
              </div>

              <div className="py-1">
                <Link
                  to="/users"
                  onClick={() => setDropdownOpen(false)}
                  className="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center justify-between transition-colors"
                >
                  <span>Role & Access Scope Directory</span>
                  <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                </Link>
                <Link
                  to="/rules"
                  onClick={() => setDropdownOpen(false)}
                  className="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center justify-between transition-colors"
                >
                  <span>APH Workflow Specifications</span>
                  <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                </Link>
              </div>

              <div className="border-t border-slate-100 pt-1 mt-1">
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    logout();
                  }}
                  className="w-full text-left px-4 py-2 text-xs text-rose-600 hover:bg-rose-50 flex items-center gap-2 font-medium transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out of Platform</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
