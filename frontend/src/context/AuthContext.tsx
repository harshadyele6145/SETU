import React, { createContext, useContext, useState } from 'react';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  institution_id?: string;
  region_id?: string;
  is_active: boolean;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  login: (email: string, password?: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const DEMO_USERS = [
  { email: 'inst_admin@fictional-nist.edu.in', role: 'INST_ADMIN', name: 'Dr. R. K. Verma', label: 'Inst Admin (North - NIST)' },
  { email: 'inst_admin2@fictional-poly.org', role: 'INST_ADMIN', name: 'Prof. S. M. Patil', label: 'Inst Admin (West - Poly)' },
  { email: 'ro_north@aicte.gov.in', role: 'RO_OFFICER', name: 'Dr. Arun Mehra', label: 'Regional Officer (RO North)' },
  { email: 'ro_west_dir@aicte.gov.in', role: 'REGIONAL_DIR', name: 'Dr. S. K. Mahajan', label: 'Regional Director (RO West)' },
  { email: 'ro_west@aicte.gov.in', role: 'RO_OFFICER', name: 'Smt. Sunita Deshmukh', label: 'Regional Officer (RO West)' },
  { email: 'bureau_officer@aicte.gov.in', role: 'BUREAU_OFFICER', name: 'Dr. Meenakshi Sundaram', label: 'Bureau Officer (HQ)' },
  { email: 'bo_officer@aicte.gov.in', role: 'BO_OFFICER', name: 'Shri Vikramaditya Sen', label: 'Bureau Officer (Legacy)' },
  { email: 'evc_coord@aicte.gov.in', role: 'EVC_COORD', name: 'Dr. Preeti Saxena', label: 'EVC Coordinator (North)' },
  { email: 'expert1@aicte-roster.ac.in', role: 'COMMITTEE_MBR', name: 'Dr. Sunita Deshmukh', label: 'Committee Member (IIT Bombay)' },
  { email: 'comm_member@aicte.gov.in', role: 'COMM_MEMBER', name: 'Prof. H. S. Murthy', label: 'Committee Member (IISc)' },
  { email: 'compliance_reviewer@aicte.gov.in', role: 'COMP_REV', name: 'Shri Vikramaditya Rao', label: 'Compliance Reviewer' },
  { email: 'comp_review@aicte.gov.in', role: 'COMP_REVIEW', name: 'Shri Rajeshwar Rao', label: 'Compliance Reviewer (Legacy)' },
  { email: 'comp_auth@aicte.gov.in', role: 'COMP_AUTH', name: 'Member Secretary (AICTE)', label: 'Competent Authority (Council)' },
  { email: 'sys_admin@aicte.gov.in', role: 'SYS_ADMIN', name: 'Administrator', label: 'System Admin (Tech Ops)' },
];

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem('setu_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('setu_token'));
  const [isLoading, setIsLoading] = useState(false);

  const login = async (email: string, password: string = 'DemoPass@2026'): Promise<boolean> => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        setIsLoading(false);
        return false;
      }
      const data = await res.json();
      const userProfile: UserProfile = {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        institution_id: data.institution_id,
        region_id: data.region_id,
        is_active: true,
      };

      setToken(data.access_token);
      setUser(userProfile);
      localStorage.setItem('setu_token', data.access_token);
      localStorage.setItem('setu_user', JSON.stringify(userProfile));
      setIsLoading(false);
      return true;
    } catch (err) {
      setIsLoading(false);
      return false;
    }
  };

  const logout = () => {
    if (token) {
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      }).catch(() => {});
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem('setu_token');
    localStorage.removeItem('setu_user');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};

