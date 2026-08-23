'use client';

import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import DuplicateCard from '../components/DuplicateCard';
import ComparisonModal from '../components/ComparisonModal';
import SandboxTester from '../components/SandboxTester';
import ApiJsonViewer from '../components/ApiJsonViewer';
import { ShieldAlert, Cpu, Search, Filter, RefreshCw, AlertOctagon, CheckCircle2, Layers } from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState('duplicates');
  const [apiData, setApiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRisk, setFilterRisk] = useState('ALL');
  const [selectedPair, setSelectedPair] = useState(null);

  const fetchDuplicates = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/find-duplicates');
      const data = await res.json();
      if (data.status === 'success') {
        setApiData(data);
      } else {
        setError('Failed to load duplicate detection data');
      }
    } catch (err) {
      console.error('Error fetching duplicates:', err);
      setError('Cannot connect to AI API route');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDuplicates();
  }, []);

  const results = apiData?.results || [];

  const filteredResults = results.filter(pair => {
    const matchesSearch =
      pair.project_a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pair.project_b.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pair.project_a.district.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRisk =
      filterRisk === 'ALL' ||
      pair.risk_level === filterRisk;

    return matchesSearch && matchesRisk;
  });

  const criticalCount = results.filter(p => p.risk_level === 'CRITICAL').length;
  const highCount = results.filter(p => p.risk_level === 'HIGH').length;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-['Inter']">
      
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        totalDuplicates={results.length}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* KPI Banner */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
            <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center shrink-0">
              <Layers className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Total Projects Scanned
              </span>
              <span className="text-2xl font-black text-slate-900">
                {apiData?.total_projects_scanned || 8}
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
            <div className="h-12 w-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center shrink-0">
              <ShieldAlert className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Flagged Duplicate Pairs
              </span>
              <span className="text-2xl font-black text-amber-600">
                {results.length}
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
            <div className="h-12 w-12 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center shrink-0">
              <AlertOctagon className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Critical Level (🔴 &gt;85%)
              </span>
              <span className="text-2xl font-black text-red-600">
                {criticalCount}
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
            <div className="h-12 w-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center shrink-0">
              <Cpu className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                REST API Endpoint
              </span>
              <span className="text-sm font-black text-emerald-700 block mt-0.5">
                /find-duplicates
              </span>
            </div>
          </div>

        </div>

        {/* Tab 1: Flagged Duplicates Feed */}
        {activeTab === 'duplicates' && (
          <div className="space-y-6">
            
            {/* Filter & Search Toolbar */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
              
              {/* Search Bar */}
              <div className="relative w-full md:w-96">
                <Search className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by project name or district..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 font-medium"
                />
              </div>

              {/* Risk Filter Pills */}
              <div className="flex items-center space-x-2 w-full md:w-auto justify-end">
                <span className="text-xs text-slate-500 font-bold mr-1 flex items-center gap-1">
                  <Filter className="h-3.5 w-3.5" /> Filter Risk:
                </span>
                
                <button
                  onClick={() => setFilterRisk('ALL')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    filterRisk === 'ALL'
                      ? 'bg-slate-900 text-white shadow'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  All ({results.length})
                </button>

                <button
                  onClick={() => setFilterRisk('CRITICAL')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    filterRisk === 'CRITICAL'
                      ? 'bg-red-600 text-white shadow'
                      : 'bg-red-50 text-red-700 hover:bg-red-100'
                  }`}
                >
                  🔴 Critical ({criticalCount})
                </button>

                <button
                  onClick={() => setFilterRisk('HIGH')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    filterRisk === 'HIGH'
                      ? 'bg-amber-500 text-slate-950 shadow'
                      : 'bg-amber-50 text-amber-800 hover:bg-amber-100'
                  }`}
                >
                  🟠 High ({highCount})
                </button>
              </div>

            </div>

            {/* Loading State */}
            {loading && (
              <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 shadow-sm space-y-4">
                <RefreshCw className="h-8 w-8 text-amber-500 animate-spin mx-auto" />
                <p className="text-sm font-bold text-slate-700">Running NLP Semantic & Spatial Proximity AI Scanning...</p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 rounded-3xl p-8 border border-red-200 text-center space-y-3">
                <AlertOctagon className="h-8 w-8 text-red-600 mx-auto" />
                <h3 className="text-base font-extrabold text-red-900">{error}</h3>
                <button
                  onClick={fetchDuplicates}
                  className="px-4 py-2 bg-red-600 text-white text-xs font-bold rounded-xl shadow hover:bg-red-700 transition-all"
                >
                  Retry Connection
                </button>
              </div>
            )}

            {/* Duplicate Cards Grid */}
            {!loading && !error && filteredResults.length > 0 && (
              <div className="space-y-6">
                {filteredResults.map(pair => (
                  <DuplicateCard
                    key={pair.pair_id}
                    pair={pair}
                    onInspect={setSelectedPair}
                  />
                ))}
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && filteredResults.length === 0 && (
              <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 shadow-sm space-y-3">
                <CheckCircle2 className="h-10 w-10 text-emerald-500 mx-auto" />
                <h3 className="text-base font-bold text-slate-900">No Flagged Duplicates Found</h3>
                <p className="text-xs text-slate-500">Try clearing search filters or scanning a different project threshold.</p>
              </div>
            )}

          </div>
        )}

        {/* Tab 2: Live AI Sandbox */}
        {activeTab === 'sandbox' && (
          <SandboxTester />
        )}

        {/* Tab 3: API JSON Output */}
        {activeTab === 'api' && (
          <ApiJsonViewer data={apiData} />
        )}

      </main>

      {/* Comparison Modal */}
      {selectedPair && (
        <ComparisonModal
          pair={selectedPair}
          onClose={() => setSelectedPair(null)}
        />
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-extrabold text-slate-900">MPLADS AI Anomaly Platform</span>
            <span>— Duplicate & Similarity Detection Module</span>
          </div>
          <div>Ministry of Statistics & Programme Implementation (MoSPI)</div>
        </div>
      </footer>

    </div>
  );
}
