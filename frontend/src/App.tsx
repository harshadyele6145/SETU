import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DemoBanner } from './components/Banner';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { GenericModulePage } from './pages/GenericModulePage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-50 text-slate-900">
        <DemoBanner />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <div className="flex flex-col flex-1 overflow-hidden">
            <Navbar />
            <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-100">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/applications" element={<GenericModulePage title="Applications & Case Tracking" moduleKey="applications" />} />
                <Route path="/timeline" element={<GenericModulePage title="Workflow Timeline & Application History" moduleKey="timeline" />} />
                <Route path="/evc" element={<GenericModulePage title="Expert Visit Committee (EVC) Management" moduleKey="evc" />} />
                <Route path="/compliance" element={<GenericModulePage title="Undertakings & Institutional Compliance" moduleKey="compliance" />} />
                <Route path="/documents" element={<GenericModulePage title="Prescribed Documents & Lease Renewals" moduleKey="documents" />} />
                <Route path="/alerts" element={<GenericModulePage title="Alerts & Escalations" moduleKey="alerts" />} />
                <Route path="/reports" element={<GenericModulePage title="Reports & Pendency Analytics" moduleKey="reports" />} />
                <Route path="/audit" element={<GenericModulePage title="Immutable Audit Trail & Cryptographic Verification" moduleKey="audit" />} />
                <Route path="/rules" element={<GenericModulePage title="Approval Process Handbook (APH) Workflow Rules" moduleKey="rules" />} />
                <Route path="/users" element={<GenericModulePage title="User & Access Scope Administration" moduleKey="users" />} />
                <Route path="/notifications-recovery" element={<GenericModulePage title="Notification Failures & Downtime Recovery" moduleKey="notifications" />} />
                <Route path="/integration" element={<GenericModulePage title="AICTE External Portal Integration Monitor" moduleKey="integration" />} />
                <Route path="/attention" element={<GenericModulePage title="Explainable Attention Engine (Priority Queue)" moduleKey="attention" />} />
                <Route path="/bottlenecks" element={<GenericModulePage title="Bottleneck & Exception Cockpit" moduleKey="bottlenecks" />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
