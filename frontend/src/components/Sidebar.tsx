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
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  className?: string;
}

export interface NavItemConfig {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>;
  roles?: string[];
}

export const navItems: NavItemConfig[] = [
  { name: 'Operations Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Applications', path: '/applications', icon: FileText },
  { name: 'Workflow Timeline', path: '/timeline', icon: GitCommit },
  { 
    name: 'EVC Management', 
    path: '/evc', 
    icon: Calendar,
    roles: ['RO_OFFICER', 'REGIONAL_DIR', 'EVC_COORD', 'COMM_MEMBER', 'COMMITTEE_MBR', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH', 'SYS_ADMIN'] 
  },
  { name: 'Undertakings & Compliance', path: '/compliance', icon: CheckSquare },
  { name: 'Documents & Renewals', path: '/documents', icon: Files },
  { name: 'Alerts & Escalations', path: '/alerts', icon: Bell },
  { 
    name: 'Attention Queue', 
    path: '/attention', 
    icon: Zap,
    roles: ['RO_OFFICER', 'REGIONAL_DIR', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH', 'SYS_ADMIN']
  },
  { 
    name: 'Bottleneck Cockpit', 
    path: '/bottlenecks', 
    icon: Gauge,
    roles: ['RO_OFFICER', 'REGIONAL_DIR', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH', 'SYS_ADMIN']
  },
  { 
    name: 'Compliance Dependencies', 
    path: '/dependencies', 
    icon: GitCommit,
    roles: ['COMP_REVIEW', 'COMP_REV', 'RO_OFFICER', 'REGIONAL_DIR', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH', 'SYS_ADMIN']
  },
  { 
    name: 'Reports & Analytics', 
    path: '/reports', 
    icon: BarChart3,
    roles: ['RO_OFFICER', 'REGIONAL_DIR', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH', 'SYS_ADMIN']
  },
  { 
    name: 'Audit Trail', 
    path: '/audit', 
    icon: ShieldCheck,
    roles: ['RO_OFFICER', 'REGIONAL_DIR', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH', 'SYS_ADMIN']
  },
  { 
    name: 'Workflow Rules', 
    path: '/rules', 
    icon: Sliders 
  },
  { 
    name: 'User & Access Admin', 
    path: '/users', 
    icon: Users,
    roles: ['SYS_ADMIN', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH']
  },
  { 
    name: 'Notification Failures', 
    path: '/notifications-recovery', 
    icon: AlertOctagon,
    roles: ['SYS_ADMIN', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH']
  },
  { 
    name: 'Integration Monitor', 
    path: '/integration', 
    icon: Network,
    roles: ['SYS_ADMIN', 'BO_OFFICER', 'BUREAU_OFFICER', 'COMP_AUTH']
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  const { user } = useAuth();

  const filteredItems = navItems.filter((item) => {
    if (!item.roles) return true;
    if (!user || !user.role) return false;
    return item.roles.includes(user.role);
  });

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
        {filteredItems.map((item) => {
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
            </NavLink>
          );
        })}
      </nav>

      <div className="p-3 border-t border-slate-800 text-xs text-slate-400">
        <div className="flex items-center justify-between">
          <span>APH 2024-27</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-teal-400 font-mono">
            v1.0.0 · Core
          </span>
        </div>
      </div>
    </aside>
  );
};
