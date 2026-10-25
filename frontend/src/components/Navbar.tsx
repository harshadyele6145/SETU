import React, { useState, useEffect } from 'react';
import { User, LogOut, CheckCircle2, AlertCircle, ChevronDown } from 'lucide-react';
import { useAuth, DEMO_USERS } from '../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user, login, logout } = useAuth();
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

        {/* Demo Persona Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 text-xs sm:text-sm bg-slate-50 hover:bg-slate-100 px-2.5 py-1.5 rounded border border-slate-200 text-slate-700 transition-colors"
            title="Switch Demo Persona Role"
            aria-expanded={dropdownOpen}
          >
            <div className="w-6 h-6 rounded-full bg-teal-600 flex items-center justify-center text-white text-xs font-semibold">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="text-left hidden sm:block">
              <div className="font-medium text-slate-900 leading-tight truncate max-w-[150px]">
                {user?.full_name || 'Select Role'}
              </div>
              <div className="text-[10px] text-teal-700 font-mono">
                {user?.role || 'Guest'}
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50">
              <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                Switch Demo Persona
              </div>
              <div className="max-h-64 overflow-y-auto">
                {DEMO_USERS.map((demo) => (
                  <button
                    key={demo.email}
                    onClick={() => {
                      login(demo.email);
                      setDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 transition-colors ${
                      user?.email === demo.email ? 'bg-teal-50 text-teal-900 font-semibold' : 'text-slate-700'
                    }`}
                  >
                    <div>
                      <div className="font-medium leading-tight">{demo.label}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{demo.role}</div>
                    </div>
                    {user?.email === demo.email && (
                      <span className="w-2 h-2 rounded-full bg-teal-600"></span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {user && (
          <button
            onClick={() => logout()}
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
