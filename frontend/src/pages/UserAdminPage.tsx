import React, { useState, useEffect } from 'react';
import { 
  Users, 
  ShieldCheck, 
  Building, 
  MapPin, 
  CheckCircle2, 
  XCircle, 
  KeyRound, 
  Award,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface UserItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  institution_id?: string;
  institution_name?: string;
  region_id?: string;
  region_name?: string;
  statutory_authority: boolean;
}

interface RoleDef {
  role_key: string;
  title: string;
  scope_level: string;
  can_approve: boolean;
  can_verify_compliance: boolean;
  can_assign_evc: boolean;
  description: string;
}

const DEMO_PERSONAS = [
  {
    role: 'INST_ADMIN',
    name: 'Dr. R. K. Verma',
    email: 'inst_admin@fictional-nist.edu.in',
    institution: 'National Institute of Science & Tech (North)',
    scope: 'Institution Only',
    demoTask: 'Submit EoA applications, upload compliance undertaking proof, register building safety certificates.'
  },
  {
    role: 'RO_OFFICER',
    name: 'Shri Amitabh Sharma',
    email: 'ro_north@aicte.gov.in',
    institution: 'AICTE Northern Regional Office (Kanpur)',
    scope: 'Northern Region',
    demoTask: 'Perform scrutiny, issue deficiency returns with mandatory reasons, evaluate resubmissions.'
  },
  {
    role: 'REGIONAL_DIR',
    name: 'Dr. S. K. Mahajan',
    email: 'ro_west_dir@aicte.gov.in',
    institution: 'AICTE Western Regional Office (Mumbai)',
    scope: 'Western Region',
    demoTask: 'Supervise regional queues, monitor regional pendency, authorize committee allocations.'
  },
  {
    role: 'BUREAU_OFFICER',
    name: 'Dr. Meenakshi Sundaram',
    email: 'bureau_officer@aicte.gov.in',
    institution: 'AICTE HQ (New Delhi)',
    scope: 'National Scope',
    demoTask: 'Oversee Bottleneck & Exception Cockpit, monitor national SLAs, resolve stuck cases.'
  },
  {
    role: 'EVC_COORD',
    name: 'Prof. Arvind Kulkarni',
    email: 'evc_coord@aicte.gov.in',
    institution: 'AICTE Western Regional Office',
    scope: 'Western Jurisdiction',
    demoTask: 'Schedule 3-member EVC inspections, select experts from roster, provide delay justifications.'
  },
  {
    role: 'COMMITTEE_MBR',
    name: 'Dr. Sunita Deshmukh',
    email: 'expert1@aicte-roster.ac.in',
    institution: 'IIT Bombay / AICTE Expert Panel',
    scope: 'Assigned Inspection Visits',
    demoTask: 'Conduct on-site inspection, verify physical infrastructure and laboratory equipment, sign off report.'
  },
  {
    role: 'COMP_REV',
    name: 'Shri Vikramaditya Rao',
    email: 'compliance_reviewer@aicte.gov.in',
    institution: 'AICTE Compliance Bureau',
    scope: 'National Regulatory Registry',
    demoTask: 'Two-step evidence verification (INV-01), accept or return condition precedent proof.'
  },
  {
    role: 'COMP_AUTH',
    name: 'Prof. T. G. Sitharam (Council Chair)',
    email: 'comp_auth@aicte.gov.in',
    institution: 'AICTE Executive Committee',
    scope: 'Sole Statutory Authority',
    demoTask: 'Exercise exclusive statutory authority (INV-03) to grant final Approval or Statutory Rejection.'
  }
];

export const UserAdminPage: React.FC = () => {
  const { user: currentUser, token, login } = useAuth();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [roles, setRoles] = useState<RoleDef[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [activeTab, setActiveTab] = useState<'users' | 'personas' | 'matrix'>('personas');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [uRes, rRes] = await Promise.all([
        fetch('/api/users', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/api/users/roles', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (uRes.ok) {
        const uData = await uRes.json();
        setUsers(uData);
      }
      if (rRes.ok) {
        const rData = await rRes.json();
        setRoles(rData);
      }
    } catch (err) {
      console.error('Failed to load user administration data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  const handleQuickLogin = async (email: string) => {
    try {
      await login(email, 'DemoPass@2026');
    } catch (err) {
      alert('Quick switch failed: ' + err);
    }
  };

  const filteredUsers = users.filter(u => {
    const matchesSearch = 
      u.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.institution_name && u.institution_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (u.region_name && u.region_name.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-teal-600" />
            User & Access Scope Administration
          </h2>
          <p className="text-xs text-slate-500">
            Multi-role RBAC enforcement, institutional & regional scoping boundaries, and quick demo persona switcher.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-50"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Accounts
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-6">
        <button
          onClick={() => setActiveTab('personas')}
          className={`pb-2.5 text-xs font-bold transition-colors border-b-2 ${
            activeTab === 'personas'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Demo Persona Switcher (8 Roles)
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`pb-2.5 text-xs font-bold transition-colors border-b-2 ${
            activeTab === 'users'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Database User Accounts ({users.length})
        </button>
        <button
          onClick={() => setActiveTab('matrix')}
          className={`pb-2.5 text-xs font-bold transition-colors border-b-2 ${
            activeTab === 'matrix'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Statutory RBAC Permission Matrix
        </button>
      </div>

      {/* TAB 1: DEMO PERSONAS */}
      {activeTab === 'personas' && (
        <div className="space-y-4">
          <div className="bg-teal-50 border border-teal-200 rounded-lg p-4 text-xs text-teal-900 flex items-start gap-3">
            <KeyRound className="w-4 h-4 text-teal-700 mt-0.5 flex-shrink-0" />
            <div>
              <span className="font-bold">Instant Demonstration Persona Switcher:</span>
              <p className="mt-0.5 text-teal-800">
                Click any persona's <strong>"Switch Persona"</strong> button to immediately authenticate as that role and demonstrate server-enforced access boundaries in real time. Default password: <code className="bg-teal-100 px-1 py-0.5 rounded font-mono">DemoPass@2026</code>.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {DEMO_PERSONAS.map((p) => {
              const isCurrent = currentUser?.email === p.email;
              return (
                <div 
                  key={p.email} 
                  className={`p-4 rounded-lg border transition-all ${
                    isCurrent 
                      ? 'border-teal-600 bg-white ring-2 ring-teal-500/20 shadow-md' 
                      : 'border-slate-200 bg-white hover:border-slate-300 shadow-sm'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">{p.name}</span>
                        {isCurrent && (
                          <span className="px-2 py-0.5 text-[10px] font-bold bg-teal-100 text-teal-800 rounded-full">
                            CURRENT
                          </span>
                        )}
                        {p.role === 'COMP_AUTH' && (
                          <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 rounded-full flex items-center gap-1">
                            <Award className="w-3 h-3" /> STATUTORY AUTH
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] font-mono text-slate-500 mt-0.5">{p.email}</p>
                    </div>
                    <span className="px-2 py-1 text-[10px] font-semibold bg-slate-100 text-slate-700 rounded border border-slate-200">
                      {p.role}
                    </span>
                  </div>

                  <div className="mt-3 space-y-1.5 text-xs text-slate-600">
                    <div className="flex items-center gap-1.5 text-[11px]">
                      <Building className="w-3.5 h-3.5 text-slate-400" />
                      <span>{p.institution}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px]">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>Boundary: <strong>{p.scope}</strong></span>
                    </div>
                    <p className="text-[11px] text-slate-500 bg-slate-50 p-2 rounded border border-slate-100 mt-2">
                      <strong className="text-slate-700">Demo Role:</strong> {p.demoTask}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex justify-end">
                    <button
                      onClick={() => handleQuickLogin(p.email)}
                      disabled={isCurrent}
                      className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                        isCurrent
                          ? 'bg-slate-100 text-slate-400 cursor-default'
                          : 'bg-teal-600 hover:bg-teal-700 text-white shadow-sm'
                      }`}
                    >
                      {isCurrent ? 'Active Persona' : 'Switch Persona'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: DATABASE USERS TABLE */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3 bg-white p-3 rounded-lg border border-slate-200">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search user by name, email, institution, or region..."
                className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="text-xs px-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500 bg-white"
              >
                <option value="ALL">All Roles (8 RBAC)</option>
                <option value="INST_ADMIN">Institution Admin</option>
                <option value="RO_OFFICER">RO Officer</option>
                <option value="REGIONAL_DIR">Regional Director</option>
                <option value="BUREAU_OFFICER">Bureau Officer</option>
                <option value="EVC_COORD">EVC Coordinator</option>
                <option value="COMMITTEE_MBR">Committee Member</option>
                <option value="COMP_REV">Compliance Reviewer</option>
                <option value="COMP_AUTH">Competent Authority</option>
              </select>
            </div>
          </div>

          {/* Users Table */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Name & Email</th>
                  <th className="py-2.5 px-4">Role Key</th>
                  <th className="py-2.5 px-4">Assigned Institution</th>
                  <th className="py-2.5 px-4">Regional Boundary</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">Statutory Authority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-slate-400">Loading accounts...</td>
                  </tr>
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-slate-400">No matching users found.</td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-4">
                        <div className="font-semibold text-slate-800">{u.full_name}</div>
                        <div className="font-mono text-[11px] text-slate-500">{u.email}</div>
                      </td>
                      <td className="py-2.5 px-4">
                        <span className="px-2 py-0.5 text-[10px] font-semibold bg-slate-100 text-slate-700 rounded border border-slate-200">
                          {u.role}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-slate-700">
                        {u.institution_name || <span className="text-slate-400">Not Applicable (Council)</span>}
                      </td>
                      <td className="py-2.5 px-4 text-slate-700">
                        {u.region_name || <span className="text-slate-400">National / AICTE HQ</span>}
                      </td>
                      <td className="py-2.5 px-4">
                        {u.is_active ? (
                          <span className="text-emerald-700 font-semibold inline-flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Active
                          </span>
                        ) : (
                          <span className="text-rose-700 font-semibold inline-flex items-center gap-1">
                            <XCircle className="w-3.5 h-3.5 text-rose-500" /> Inactive
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-4">
                        {u.statutory_authority ? (
                          <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 rounded inline-flex items-center gap-1">
                            <Award className="w-3 h-3 text-amber-700" /> SOLE STATUTORY POWER
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Workflow Operator</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: STATUTORY RBAC MATRIX */}
      {activeTab === 'matrix' && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-600" />
              Statutory Roles and Permission Boundaries (8 RBAC Roles)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Strictly enforced server-side via FastAPI dependency injection and database foreign-key scoping.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Role Key</th>
                  <th className="py-2.5 px-4">Designation</th>
                  <th className="py-2.5 px-4">Enforced Scope</th>
                  <th className="py-2.5 px-4 text-center">Verify Undertakings</th>
                  <th className="py-2.5 px-4 text-center">Assign EVC</th>
                  <th className="py-2.5 px-4 text-center">Final Approval</th>
                  <th className="py-2.5 px-4">Regulatory Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {roles.map((r) => (
                  <tr key={r.role_key} className="hover:bg-slate-50">
                    <td className="py-2.5 px-4 font-mono font-bold text-slate-700">{r.role_key}</td>
                    <td className="py-2.5 px-4 font-semibold text-slate-800">{r.title}</td>
                    <td className="py-2.5 px-4 text-slate-600">{r.scope_level}</td>
                    <td className="py-2.5 px-4 text-center">
                      {r.can_verify_compliance ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 mx-auto" />
                      ) : (
                        <span className="text-slate-300 font-bold">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      {r.can_assign_evc ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 mx-auto" />
                      ) : (
                        <span className="text-slate-300 font-bold">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      {r.can_approve ? (
                        <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 rounded border border-amber-300">
                          STATUTORY
                        </span>
                      ) : (
                        <span className="text-slate-300 font-bold">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-slate-600 max-w-sm text-[11px]">{r.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
