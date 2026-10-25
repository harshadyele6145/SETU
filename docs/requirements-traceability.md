# SETU — Requirements Traceability Matrix (RTM)

| Requirement ID | Description | Priority | Backend Implementation | Frontend UI Component | Automated Test Suite | Demo Step | Status |
|---|---|---|---|---|---|---|---|
| **REQ-F01** | Auth, RBAC & Scope Enforcement | P0 | `app/api/auth.py`, `app/core/security.py`, `app/services/auth_service.py` | `frontend/src/pages/Login.tsx`, `frontend/src/context/AuthContext.tsx` | `tests/test_auth.py`, `tests/test_security_scopes.py` | Demo G | IMPLEMENTED (M2) |
| **REQ-F02** | Multi-Route Workflow Engine | P0 | `app/services/workflow_engine.py`, `app/api/applications.py` | `frontend/src/pages/Applications.tsx`, `frontend/src/pages/ApplicationDetail.tsx` | `tests/test_workflow.py` | Demo A, Demo B | IMPLEMENTED (M3) |
| **REQ-F03** | Compliance & Undertakings | P0 | `app/services/compliance_service.py`, `app/api/compliance.py` | `frontend/src/pages/Compliance.tsx`, `frontend/src/components/EvidenceModal.tsx` | `tests/test_compliance.py` | Demo D | IMPLEMENTED (M4) |
| **REQ-F04** | Document Validity & Renewal | P0 | `app/services/document_service.py`, `app/api/documents.py`, `app/core/storage.py` | `frontend/src/pages/Documents.tsx` | `tests/test_documents.py` | Demo E | IMPLEMENTED (M4) |
| **REQ-F05** | Deadlines, Alerts & Escalation | P0 | `app/services/deadline_service.py`, `app/services/alert_service.py`, `app/api/alerts.py` | `frontend/src/pages/Alerts.tsx`, `frontend/src/pages/NotificationRecovery.tsx` | `tests/test_deadlines.py`, `tests/test_alerts.py` | Demo F | IMPLEMENTED (M5) |
| **REQ-F06** | Audit Trail & Hash-Chaining | P0 | `app/services/audit_service.py`, `app/api/audit.py` | `frontend/src/pages/AuditTrail.tsx` | `tests/test_audit_hashchain.py` | Demo H | IMPLEMENTED (M3) |
| **REQ-F07** | Live Dashboards & Reporting | P1 | `app/services/dashboard_service.py`, `app/api/dashboard.py` | `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Reports.tsx` | `tests/test_dashboard.py` | Demo H | IMPLEMENTED (M6) |
| **REQ-F08** | EVC Operations Management | P1 | `app/services/evc_service.py`, `app/api/evc.py` | `frontend/src/pages/EVCManagement.tsx` | `tests/test_evc.py` | Demo C | IMPLEMENTED (M6) |
| **REQ-F09** | Explainable Attention Engine | P1 | `app/services/attention_engine.py`, `app/api/attention.py` | `frontend/src/pages/AttentionQueue.tsx` | `tests/test_attention_engine.py` | Demo I | IMPLEMENTED (M7) |
| **REQ-F10** | Bottleneck & Exception Cockpit | P1 | `app/services/bottleneck_service.py`, `app/api/bottleneck.py` | `frontend/src/pages/BottleneckCockpit.tsx` | `tests/test_bottlenecks.py` | Demo I | IMPLEMENTED (M7) |
| **REQ-F11** | Compliance Dependency View | P2 | `app/services/dependency_service.py` | `frontend/src/pages/ComplianceDependencies.tsx` | `tests/test_compliance.py` | Demo D | IMPLEMENTED (M7) |
| **REQ-F12** | Explainable Case Summarizer | P2 | `app/services/summary_service.py` | `frontend/src/components/CaseSummaryCard.tsx` | `tests/test_workflow.py` | Demo A | IMPLEMENTED (M7) |
| **REQ-F13** | External Portal Adapter & Mock | P2 | `app/adapters/external_portal.py` | `frontend/src/pages/IntegrationMonitor.tsx` | `tests/test_portal_adapter.py` | Integration check | IMPLEMENTED (M1) |

