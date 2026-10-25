import React, { useState, useEffect } from 'react';
import { User, LogOut, CheckCircle2, AlertCircle } from 'lucide-react';

interface NavbarProps {
  currentUser?: {
    full_name: string;
    role: string;
    scope?: string;
  };
  onLogout?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentUser, onLogout }) => {
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

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
    <header className="h-14 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between shrink-0 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800 text-sm sm:text-base hidden sm:inline">
            All India Council for Technical Education
          </span>
          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-300 font-mono">
            SETU Platform
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 sm:gap-4">
        {/* Backend health indicator */}
        <div 
          className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border"
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

        {/* User Scope badge */}
        <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-700">
          <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-slate-600">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden sm:block text-left">
            <div className="font-medium text-slate-900 leading-tight">
              {currentUser?.full_name || 'Dr. K. S. Sharma'}
            </div>
            <div className="text-[11px] text-teal-700 font-mono">
              {currentUser?.role || 'RO_OFFICER'} {currentUser?.scope ? `(${currentUser.scope})` : ''}
            </div>
          </div>
        </div>

        {onLogout && (
          <button
            onClick={onLogout}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded transition-colors"
            title="Log Out"
            aria-label="Log Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  );
};
