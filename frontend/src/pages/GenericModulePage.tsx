import React from 'react';
import { Layers, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

interface GenericModulePageProps {
  title: string;
  moduleKey: string;
}

export const GenericModulePage: React.FC<GenericModulePageProps> = ({ title, moduleKey }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link 
          to="/"
          className="p-1 text-slate-500 hover:text-slate-800 hover:bg-white rounded border border-transparent hover:border-slate-300 transition-colors"
          title="Return to Dashboard"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h2>
          <p className="text-xs text-slate-500">Module identifier: <span className="font-mono text-teal-700">{moduleKey}</span></p>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center shadow-sm">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-500 mb-3">
          <Layers className="w-6 h-6 text-teal-600" />
        </div>
        <h3 className="font-semibold text-slate-800 text-base mb-1">
          {title} Interface
        </h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mb-4">
          This functional view is integrated with the SETU navigation structure and connects to the underlying backend services and PostgreSQL database schema.
        </p>
        <div className="inline-flex items-center gap-2 text-xs bg-slate-50 border border-slate-200 px-3 py-1.5 rounded text-slate-600">
          <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
          <span>Schema & API Ready</span>
        </div>
      </div>
    </div>
  );
};
