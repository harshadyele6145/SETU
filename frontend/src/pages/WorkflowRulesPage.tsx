import React, { useState } from 'react';
import { 
  BookOpen, 
  GitBranch, 
  ShieldCheck, 
  Clock
} from 'lucide-react';

export const WorkflowRulesPage: React.FC = () => {
  const [selectedRoute, setSelectedRoute] = useState<'A' | 'B' | 'C' | 'D'>('A');

  const routes = {
    A: {
      name: 'Route A — New Technical Institution Setup',
      aph_ref: 'APH 2026-2027 Chapter I',
      stages: [
        { code: 'DRAFT', name: 'Draft Application Dossier', sla: 'Institutional' },
        { code: 'SUBMITTED', name: 'Application Formally Submitted', sla: '1 day' },
        { code: 'UNDER_SCRUTINY', name: 'Document Scrutiny Committee', sla: '15 days' },
        { code: 'SCRUTINY_RECOMMENDED', name: 'Scrutiny Clear / Recommended', sla: '3 days' },
        { code: 'EVC_SCHEDULED', name: 'Expert Visit Committee (On-Site)', sla: '10 days' },
        { code: 'EVC_COMPLETED', name: 'EVC Report Upload & Assessment', sla: '5 days' },
        { code: 'SAC_RECOMMENDED', name: 'Standing Hearing Committee (SAC/SHC)', sla: '7 days' },
        { code: 'APPROVED', name: 'Final Statutory Approval (COMP_AUTH)', sla: 'Statutory' }
      ],
      description: 'Applicable for establishment of new technical institutions offering Degree/Diploma programs in Engineering, Technology, Management, MCA, Pharmacy, Architecture, Planning, Applied Arts, and Hotel Management.'
    },
    B: {
      name: 'Route B — Autonomous & Accredited Institutions (EoA)',
      aph_ref: 'APH 2026-2027 Chapter II',
      stages: [
        { code: 'DRAFT', name: 'Institutional Self-Disclosure', sla: 'Institutional' },
        { code: 'SUBMITTED', name: 'Self-Declaration Submitted', sla: '1 day' },
        { code: 'UNDER_SCRUTINY', name: 'Automated Norm Conformance', sla: '5 days' },
        { code: 'SCRUTINY_RECOMMENDED', name: 'Fast-Track Scrutiny Clear', sla: '2 days' },
        { code: 'APPROVED', name: 'Extension of Approval Granted', sla: 'Statutory' }
      ],
      description: 'Streamlined approval for institutions with valid NBA/NAAC accreditation or autonomous status, bypassing physical EVC inspection unless specific complaints are received.'
    },
    C: {
      name: 'Route C — Expansion, Division Addition & Supernumerary Seats',
      aph_ref: 'APH 2026-2027 Chapter III',
      stages: [
        { code: 'DRAFT', name: 'Expansion Proposal Dossier', sla: 'Institutional' },
        { code: 'SUBMITTED', name: 'Proposal Submitted', sla: '1 day' },
        { code: 'UNDER_SCRUTINY', name: 'Faculty Cadre & Built-up Scrutiny', sla: '10 days' },
        { code: 'EVC_SCHEDULED', name: 'Physical Verification of Added Labs', sla: '10 days' },
        { code: 'SAC_RECOMMENDED', name: 'Standing Hearing Committee Review', sla: '5 days' },
        { code: 'APPROVED', name: 'Expansion Approval Granted', sla: 'Statutory' }
      ],
      description: 'Applicable for existing approved institutions seeking introduction of new courses, increase in intake, second shift, NRI/FN/OCI supernumerary quotas, and integrated programs.'
    },
    D: {
      name: 'Route D — Closure, Change of Site, Affiliation or Trust',
      aph_ref: 'APH 2026-2027 Chapter IV & V',
      stages: [
        { code: 'DRAFT', name: 'Restructuring Application', sla: 'Institutional' },
        { code: 'SUBMITTED', name: 'Formal Application Submitted', sla: '1 day' },
        { code: 'UNDER_SCRUTINY', name: 'State Govt & University NOC Scrutiny', sla: '15 days' },
        { code: 'SAC_RECOMMENDED', name: 'Standing Hearing Committee', sla: '7 days' },
        { code: 'APPROVED', name: 'Restructuring Clearance Issued', sla: 'Statutory' }
      ],
      description: 'Governs institutional restructuring, progressive or complete closure, change of campus site, change of sponsoring trust/society, and merger of multiple institutions.'
    }
  };

  const active = routes[selectedRoute];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-teal-700" />
            Approval Process Handbook (APH) Workflow Rules
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Formal regulatory finite state machines for Routes A, B, C, D and statutory non-negotiables
          </p>
        </div>
      </div>

      {/* Non-Negotiable Invariants Alert */}
      <div className="p-4 bg-navy-900 text-white rounded-lg border border-navy-700 shadow space-y-2">
        <div className="font-bold text-xs sm:text-sm text-teal-400 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4" />
          Regulatory Integrity Invariants Encoded in SETU
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-300 pt-1">
          <div className="p-2.5 bg-navy-800 rounded border border-navy-600 space-y-1">
            <span className="font-mono text-teal-300 font-bold">INV-01: Two-Step Evidence</span>
            <p className="text-[11px] text-slate-300">
              Uploaded compliance evidence enters state <code className="text-teal-300">SUBMITTED</code>. Verification requires explicit review and audit signature by an authorized officer.
            </p>
          </div>

          <div className="p-2.5 bg-navy-800 rounded border border-navy-600 space-y-1">
            <span className="font-mono text-teal-300 font-bold">INV-02: Mandatory Deficiency Log</span>
            <p className="text-[11px] text-slate-300">
              Returning an application for clarification strictly requires specific deficiency comments. Resubmission increments <code className="text-teal-300">return_count</code>.
            </p>
          </div>

          <div className="p-2.5 bg-navy-800 rounded border border-navy-600 space-y-1">
            <span className="font-mono text-teal-300 font-bold">INV-03: Statutory Finality</span>
            <p className="text-[11px] text-slate-300">
              Final approval or rejection is strictly restricted to the Competent Authority (<code className="text-teal-300">COMP_AUTH</code>). Regional Officers cannot issue final orders.
            </p>
          </div>
        </div>
      </div>

      {/* Route Switcher */}
      <div className="flex flex-wrap gap-2">
        {(['A', 'B', 'C', 'D'] as const).map((r) => (
          <button
            key={r}
            onClick={() => setSelectedRoute(r)}
            className={`px-4 py-2 rounded-lg text-xs sm:text-sm font-bold border transition-colors ${
              selectedRoute === r
                ? 'bg-teal-700 text-white border-teal-700 shadow-sm'
                : 'bg-white text-slate-700 hover:bg-slate-50 border-slate-300'
            }`}
          >
            Route {r}
          </button>
        ))}
      </div>

      {/* Selected Route Details */}
      <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm space-y-5">
        <div className="border-b pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <h3 className="text-base sm:text-lg font-bold text-slate-900">{active.name}</h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200">
              {active.aph_ref}
            </span>
          </div>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">{active.description}</p>
        </div>

        {/* Stages Timeline */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            <GitBranch className="w-4 h-4 text-teal-700" />
            Sequential Stage State Machine & Prescribed SLAs
          </h4>

          <div className="relative pl-6 border-l-2 border-teal-200 space-y-4">
            {active.stages.map((stg, sIdx) => (
              <div key={stg.code} className="relative group">
                {/* Circle marker */}
                <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-teal-600 border-2 border-white shadow-xs" />

                <div className="p-3 bg-slate-50 rounded border flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                      <span>Step {sIdx + 1}: {stg.name}</span>
                      <span className="font-mono text-[10px] text-teal-700">({stg.code})</span>
                    </div>
                  </div>

                  <div className="text-right text-xs">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white border text-slate-600 font-mono text-[11px]">
                      <Clock className="w-3 h-3 text-slate-400" /> SLA: {stg.sla}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
