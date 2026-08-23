import React, { useState } from 'react';
import { Database, Copy, Check, Terminal, ExternalLink } from 'lucide-react';

export default function ApiJsonViewer({ data }) {
  const [copied, setCopied] = useState(false);

  const jsonString = JSON.stringify(data, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="bg-slate-900 text-white rounded-3xl p-8 shadow-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <Terminal className="h-5 w-5 text-amber-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
              Person 3 Deliverable API Payload
            </span>
          </div>
          <h2 className="text-2xl font-black text-slate-100">
            /find-duplicates REST Endpoint Payload
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            This structured JSON output feeds directly into Person 6's Risk Engine. It contains multi-factor similarity metrics, composite risk scores, and human-readable explainability descriptions for every flagged duplicate pair.
          </p>
        </div>

        <button
          onClick={handleCopy}
          className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl flex items-center space-x-2 transition-all shadow"
        >
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          <span>{copied ? 'Copied JSON Payload!' : 'Copy JSON for Person 6'}</span>
        </button>
      </div>

      {/* JSON Code Viewer Container */}
      <div className="bg-slate-950 rounded-3xl p-6 border border-slate-800 shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4 text-xs font-mono text-slate-400">
          <div className="flex items-center space-x-2">
            <span className="h-3 w-3 rounded-full bg-red-500 inline-block"></span>
            <span className="h-3 w-3 rounded-full bg-yellow-500 inline-block"></span>
            <span className="h-3 w-3 rounded-full bg-green-500 inline-block"></span>
            <span className="ml-2 text-slate-300 font-bold">GET http://localhost:5000/find-duplicates</span>
          </div>
          <span>Content-Type: application/json</span>
        </div>

        <pre className="text-xs font-mono text-emerald-400 overflow-x-auto max-h-[600px] p-4 bg-slate-900/60 rounded-2xl border border-slate-800/80 leading-relaxed">
          <code>{jsonString}</code>
        </pre>
      </div>
    </div>
  );
}
