import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { TimelinePage } from './pages/TimelinePage';
import { CompliancePage } from './pages/CompliancePage';
import { DocumentsPage } from './pages/DocumentsPage';
import { EVCManagementPage } from './pages/EVCManagementPage';
import { ReportsPage } from './pages/ReportsPage';
import { AlertsPage } from './pages/AlertsPage';
import { NotificationRecoveryPage } from './pages/NotificationRecoveryPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { AttentionQueuePage } from './pages/AttentionQueuePage';
import { BottleneckCockpitPage } from './pages/BottleneckCockpitPage';
import { WorkflowRulesPage } from './pages/WorkflowRulesPage';
import { ComplianceDependenciesPage } from './pages/ComplianceDependenciesPage';
import { IntegrationMonitorPage } from './pages/IntegrationMonitorPage';
import { UserAdminPage } from './pages/UserAdminPage';

const AppWorkspace: React.FC = () => {
  const { user, token } = useAuth();

  if (!token || !user) {
    return <LoginPage />;
  }

  return (
    <BrowserRouter>
      <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-50 text-slate-900">
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <div className="flex flex-col flex-1 overflow-hidden">
            <Navbar />
            <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-100">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/applications" element={<ApplicationsPage />} />
                <Route path="/timeline" element={<TimelinePage />} />
                <Route path="/evc" element={<EVCManagementPage />} />
                <Route path="/compliance" element={<CompliancePage />} />
                <Route path="/documents" element={<DocumentsPage />} />
                <Route path="/alerts" element={<AlertsPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/audit" element={<AuditTrailPage />} />
                <Route path="/rules" element={<WorkflowRulesPage />} />
                <Route path="/users" element={<UserAdminPage />} />
                <Route path="/notifications-recovery" element={<NotificationRecoveryPage />} />
                <Route path="/integration" element={<IntegrationMonitorPage />} />
                <Route path="/attention" element={<AttentionQueuePage />} />
                <Route path="/bottlenecks" element={<BottleneckCockpitPage />} />
                <Route path="/dependencies" element={<ComplianceDependenciesPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            {/* Discreet Truthful Footer */}
            <footer className="h-7 bg-slate-900 border-t border-slate-800 px-4 flex items-center justify-between text-[11px] text-slate-400 select-none shrink-0">
              <span className="font-medium text-slate-300">SETU — AICTE Approval Operations Platform</span>
              <span className="text-slate-500 hidden sm:inline">SETU Prototype · Sample Data · Fictional Regulatory Records for Evaluation</span>
            </footer>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppWorkspace />
    </AuthProvider>
  );
};

export default App;
