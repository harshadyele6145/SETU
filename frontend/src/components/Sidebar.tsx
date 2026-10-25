import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  GitCommit,
  Calendar,
  CheckSquare,
  Files,
  Bell,
  BarChart3,
  ShieldCheck,
  Sliders,
  Users,
  AlertOctagon,
  Network,
  Zap,
  Gauge
} from 'lucide-react';

interface SidebarProps {
  className?: string;
}

export const navItems = [
  { name: 'Operations Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Applications', path: '/applications', icon: FileText },
  { name: 'Workflow Timeline', path: '/timeline', icon: GitCommit },
  { name: 'EVC Management', path: '/evc', icon: Calendar },
  { name: 'Undertakings & Compliance', path: '/compliance', icon: CheckSquare },
  { name: 'Documents & Renewals', path: '/documents', icon: Files },
  { name: 'Alerts & Escalations', path: '/alerts', icon: Bell },
  { name: 'Reports & Analytics', path: '/reports', icon: BarChart3 },
  { name: 'Audit Trail', path: '/audit', icon: ShieldCheck },
  { name: 'Workflow Rules', path: '/rules', icon: Sliders },
  { name: 'User & Access Admin', path: '/users', icon: Users },
  { name: 'Notification Failures', path: '/notifications-recovery', icon: AlertOctagon },
  { name: 'Integration Monitor', path: '/integration', icon: Network },
  { name: 'Compliance Dependencies', path: '/dependencies', icon: GitCommit, badge: 'P2 Depth' },
  { name: 'Attention Queue', path: '/attention', icon: Zap, badge: 'P1 Innovation' },
  { name: 'Bottleneck Cockpit', path: '/bottlenecks', icon: Gauge, badge: 'P1 Innovation' },
];

export const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  return (
    <aside 
      className={`w-64 bg-slate-900 text-slate-100 flex flex-col shrink-0 border-r border-slate-800 ${className}`}
      aria-label="Sidebar Navigation"
    >
      <div className="p-4 border-b border-slate-800 flex items-center gap-3">
        <div className="w-9 h-9 rounded bg-teal-600 flex items-center justify-center font-bold text-lg text-white shadow">
          S
        </div>
        <div>
          <h1 className="font-bold text-base tracking-tight text-white leading-tight">SETU</h1>
          <p className="text-xs text-slate-400">AICTE Approval Ops</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded text-xs sm:text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-teal-700 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0 text-slate-400 group-hover:text-white" aria-hidden="true" />
              <span className="truncate flex-1">{item.name}</span>
              {item.badge && (
                <span className="text-[10px] bg-teal-900 text-teal-300 px-1.5 py-0.5 rounded font-mono">
                  {item.badge.split(' ')[0]}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="p-3 border-t border-slate-800 text-xs text-slate-400">
        <div className="flex items-center justify-between">
          <span>APH 2024-27</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-teal-400">
            SIH26262
          </span>
        </div>
      </div>
    </aside>
  );
};

