import React, { useState, useEffect } from 'react';
import { 
  Network, 
  Building2, 
  FileText, 
  ShieldCheck, 
  Files, 
  RotateCcw
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface Node {
  id: string;
  label: string;
  type: string;
  status: string;
}

interface Link {
  source: string;
  target: string;
  relationship: string;
}

interface DependencyGraph {
  nodes: Node[];
  links: Link[];
}

export const ComplianceDependenciesPage: React.FC = () => {
  const { token } = useAuth();
  const [graph, setGraph] = useState<DependencyGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const fetchGraph = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/bottlenecks/dependencies', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setGraph(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch compliance dependencies');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [token]);

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'INSTITUTION':
        return <Building2 className="w-4 h-4 text-navy-800" />;
      case 'APPLICATION':
        return <FileText className="w-4 h-4 text-teal-700" />;
      case 'COMPLIANCE_OBLIGATION':
        return <ShieldCheck className="w-4 h-4 text-amber-600" />;
      default:
        return <Files className="w-4 h-4 text-purple-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
      case 'VERIFIED':
      case 'VALID':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'OVERDUE':
      case 'EXPIRED':
      case 'REJECTED':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'DUE_SOON':
      case 'EXPIRING_SOON':
      case 'DEFICIENT':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  const institutions = graph ? graph.nodes.filter((n) => n.type === 'INSTITUTION') : [];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Network className="w-6 h-6 text-teal-700" />
            Compliance & Document Dependency Navigator
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            End-to-end relational visualization linking Institutions &rarr; Approval Applications &rarr; Conditions Precedent &rarr; Statutory Deeds
          </p>
        </div>

        <button
          onClick={fetchGraph}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded shadow-sm transition-colors"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-teal-600 ${loading ? 'animate-spin' : ''}`} />
          <span>Reload Graph</span>
        </button>
      </div>

      {loading ? (
        <div className="p-16 text-center text-xs text-slate-500 bg-white rounded-lg border">
          Traversing compliance relational hierarchies...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 rounded-lg border border-rose-200">
          Error: {error}
        </div>
      ) : graph ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Tree Hierarchy */}
          <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm border-b pb-2 flex items-center justify-between">
              <span>Institutional Dependency Trees ({institutions.length} Institutions)</span>
              <span className="text-[11px] text-slate-400 font-normal">Click node to inspect</span>
            </h3>

            <div className="space-y-4">
              {institutions.map((instNode) => {
                const childAppLinks = graph.links.filter((l) => l.source === instNode.id && l.relationship === 'OWNS_APPLICATION');
                const childApps = graph.nodes.filter((n) => childAppLinks.some((l) => l.target === n.id));

                const childDocLinks = graph.links.filter((l) => l.source === instNode.id && l.relationship === 'HOLDS_DOCUMENT');
                const childDocs = graph.nodes.filter((n) => childDocLinks.some((l) => l.target === n.id));

                return (
                  <div key={instNode.id} className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 space-y-3">
                    {/* Institution Root Node */}
                    <div
                      onClick={() => setSelectedNode(instNode)}
                      className="cursor-pointer flex items-center justify-between p-2.5 bg-white rounded border border-slate-200 shadow-2xs hover:border-teal-500 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        {getNodeIcon('INSTITUTION')}
                        <span className="font-bold text-slate-900 text-xs sm:text-sm">{instNode.label}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border">
                        INSTITUTION
                      </span>
                    </div>

                    {/* Applications & Nested Obligations */}
                    <div className="pl-6 border-l-2 border-teal-300 ml-4 space-y-2.5">
                      <div className="text-[11px] font-bold text-teal-800 uppercase tracking-wide">
                        Approval Applications & Obligations:
                      </div>

                      {childApps.length === 0 ? (
                        <div className="text-[11px] text-slate-400 italic">No applications on record</div>
                      ) : (
                        childApps.map((appNode) => {
                          const childObLinks = graph.links.filter((l) => l.source === appNode.id && l.relationship === 'CONDITIONAL_ON');
                          const childObs = graph.nodes.filter((n) => childObLinks.some((l) => l.target === n.id));

                          return (
                            <div key={appNode.id} className="space-y-2">
                              {/* Application Node */}
                              <div
                                onClick={() => setSelectedNode(appNode)}
                                className="cursor-pointer flex items-center justify-between p-2 bg-white rounded border hover:border-teal-400 transition-colors"
                              >
                                <div className="flex items-center gap-2">
                                  {getNodeIcon('APPLICATION')}
                                  <span className="font-semibold text-slate-800 text-xs">{appNode.label}</span>
                                </div>
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(appNode.status)}`}>
                                  {appNode.status}
                                </span>
                              </div>

                              {/* Nested Obligations */}
                              {childObs.length > 0 && (
                                <div className="pl-5 border-l-2 border-amber-300 ml-4 space-y-1.5">
                                  {childObs.map((obNode) => (
                                    <div
                                      key={obNode.id}
                                      onClick={() => setSelectedNode(obNode)}
                                      className="cursor-pointer flex items-center justify-between p-1.5 bg-amber-50/50 rounded border border-amber-200/60 text-xs hover:border-amber-400 transition-colors"
                                    >
                                      <div className="flex items-center gap-1.5 truncate">
                                        {getNodeIcon('COMPLIANCE_OBLIGATION')}
                                        <span className="text-slate-800 truncate">{obNode.label}</span>
                                      </div>
                                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold border shrink-0 ${getStatusBadge(obNode.status)}`}>
                                        {obNode.status}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })
                      )}

                      {/* Prescribed Documents */}
                      <div className="pt-2">
                        <div className="text-[11px] font-bold text-purple-800 uppercase tracking-wide mb-1.5">
                          Prescribed Documents & Deeds ({childDocs.length}):
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                          {childDocs.map((docNode) => (
                            <div
                              key={docNode.id}
                              onClick={() => setSelectedNode(docNode)}
                              className="cursor-pointer p-1.5 bg-purple-50/40 rounded border border-purple-200 text-xs flex items-center justify-between hover:border-purple-400 transition-colors"
                            >
                              <div className="flex items-center gap-1.5 truncate">
                                {getNodeIcon('PRESCRIBED_DOCUMENT')}
                                <span className="text-slate-800 truncate">{docNode.label}</span>
                              </div>
                              <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold border shrink-0 ${getStatusBadge(docNode.status)}`}>
                                {docNode.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Node Inspector Panel */}
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4 h-fit">
            <h3 className="font-bold text-slate-800 text-sm border-b pb-2">
              Dependency Node Inspector
            </h3>

            {selectedNode ? (
              <div className="space-y-3 text-xs">
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Entity Type</div>
                  <div className="font-bold text-slate-900 text-sm mt-0.5">{selectedNode.type}</div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Identifier / Label</div>
                  <div className="font-semibold text-slate-800 mt-0.5">{selectedNode.label}</div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Current Status</div>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold border mt-0.5 ${getStatusBadge(selectedNode.status)}`}>
                    {selectedNode.status}
                  </span>
                </div>

                <div className="pt-2 border-t">
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Internal Node Ref</div>
                  <div className="font-mono text-[10px] text-slate-500 break-all">{selectedNode.id}</div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-400 italic">
                Select any node in the tree hierarchy to inspect its regulatory relationship and active state.
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
};
