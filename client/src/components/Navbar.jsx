import React from 'react';
import { ShieldAlert, Cpu, Database, Play, Sparkles } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, apiStatus, totalDuplicates }) {
  return (
    <header className="bg-slate-900 text-white shadow-xl border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Brand & Emblem */}
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-amber-500 via-orange-500 to-red-600 flex items-center justify-center shadow-lg shadow-orange-500/20 ring-2 ring-orange-400/30">
              <Cpu className="h-7 w-7 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="bg-orange-500/20 text-orange-400 border border-orange-500/30 text-xs font-bold px-2.5 py-0.5 rounded-md uppercase tracking-wider">
                  Person 3 — AI Module
                </span>
                <span className="flex items-center text-xs text-emerald-400 font-medium">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
                  Ready for Person 6 Risk Engine
                </span>
              </div>
              <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2 mt-0.5">
                MPLADS Duplicate & Similarity AI Engine
              </h1>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-2 bg-slate-800/80 p-1.5 rounded-xl border border-slate-700/60">
            <button
              onClick={() => setActiveTab('duplicates')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'duplicates'
                  ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <ShieldAlert className="h-4 w-4" />
              <span>Flagged Duplicates</span>
              {totalDuplicates > 0 && (
                <span className="ml-1.5 bg-red-950 text-red-300 border border-red-800 text-xs px-2 py-0.5 rounded-full font-bold">
                  {totalDuplicates}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('sandbox')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'sandbox'
                  ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Sparkles className="h-4 w-4" />
              <span>AI Sandbox Tester</span>
            </button>

            <button
              onClick={() => setActiveTab('api')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'api'
                  ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Database className="h-4 w-4" />
              <span>API JSON Output (/find-duplicates)</span>
            </button>
          </nav>

        </div>
      </div>
    </header>
  );
}
