'use client';

import React, { useState } from 'react';
import { Sparkles, RefreshCw } from 'lucide-react';
import GeoDistanceMap from './GeoDistanceMap';

export default function SandboxTester() {
  const [projA, setProjA] = useState({
    id: 'CUSTOM-PROJ-A',
    title: 'Construction of community hall in Village X',
    description: 'Construction of community hall in Village X',
    category: 'Community Infrastructure',
    sanction_amount: 1500000,
    coordinates: { lat: 25.3176, lng: 82.9739 },
    execution_start: '2024-02-01',
    execution_end: '2024-08-30'
  });

  const [projB, setProjB] = useState({
    id: 'CUSTOM-PROJ-B',
    title: 'Development of public community centre in Village X',
    description: 'Development of public community centre in Village X',
    category: 'Community Infrastructure',
    sanction_amount: 1450000,
    coordinates: { lat: 25.3180, lng: 82.9741 },
    execution_start: '2024-04-01',
    execution_end: '2024-11-30'
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleTestExample = () => {
    setProjA({
      id: 'CUSTOM-PROJ-A',
      title: 'Construction of community hall in Village X',
      description: 'Construction of community hall in Village X',
      category: 'Community Infrastructure',
      sanction_amount: 1500000,
      coordinates: { lat: 25.3176, lng: 82.9739 },
      execution_start: '2024-02-01',
      execution_end: '2024-08-30'
    });

    setProjB({
      id: 'CUSTOM-PROJ-B',
      title: 'Development of public community centre in Village X',
      description: 'Development of public community centre in Village X',
      category: 'Community Infrastructure',
      sanction_amount: 1450000,
      coordinates: { lat: 25.3180, lng: 82.9741 },
      execution_start: '2024-04-01',
      execution_end: '2024-11-30'
    });
    setResult(null);
  };

  const handleRunAiComparison = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/compare-pair', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectA: projA, projectB: projB })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setResult(data.analysis);
      }
    } catch (err) {
      console.error('Error running AI comparison:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Sandbox Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-8 shadow-xl border border-indigo-900/50">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-extrabold px-3 py-1 rounded-lg uppercase tracking-wider mb-2 inline-block">
              Interactive AI Sandbox
            </span>
            <h2 className="text-2xl font-black text-slate-100">Live Next.js AI Duplicate Tester & Simulator</h2>
            <p className="text-sm text-slate-300 max-w-2xl mt-1">
              Enter any 2 custom project titles, descriptions, and GPS coordinates to run Person 3's multi-factor AI similarity engine live.
            </p>
          </div>

          <button
            onClick={handleTestExample}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-bold rounded-xl border border-slate-700 flex items-center space-x-2 transition-all"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Load Standard Example</span>
          </button>
        </div>
      </div>

      {/* Form Inputs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Input Project A */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
            <span className="h-3 w-3 rounded-full bg-blue-600"></span>
            <h3 className="text-sm font-bold text-slate-900">Project A Definition</h3>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Project Title</label>
            <input
              type="text"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={projA.title}
              onChange={e => setProjA({ ...projA, title: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Description</label>
            <textarea
              rows={3}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={projA.description}
              onChange={e => setProjA({ ...projA, description: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">Latitude</label>
              <input
                type="number"
                step="0.0001"
                className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={projA.coordinates.lat}
                onChange={e => setProjA({ ...projA, coordinates: { ...projA.coordinates, lat: parseFloat(e.target.value) || 0 } })}
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">Longitude</label>
              <input
                type="number"
                step="0.0001"
                className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={projA.coordinates.lng}
                onChange={e => setProjA({ ...projA, coordinates: { ...projA.coordinates, lng: parseFloat(e.target.value) || 0 } })}
              />
            </div>
          </div>
        </div>

        {/* Input Project B */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
            <span className="h-3 w-3 rounded-full bg-indigo-600"></span>
            <h3 className="text-sm font-bold text-slate-900">Project B Definition</h3>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Project Title</label>
            <input
              type="text"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              value={projB.title}
              onChange={e => setProjB({ ...projB, title: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Description</label>
            <textarea
              rows={3}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              value={projB.description}
              onChange={e => setProjB({ ...projB, description: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">Latitude</label>
              <input
                type="number"
                step="0.0001"
                className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                value={projB.coordinates.lat}
                onChange={e => setProjB({ ...projB, coordinates: { ...projB.coordinates, lat: parseFloat(e.target.value) || 0 } })}
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">Longitude</label>
              <input
                type="number"
                step="0.0001"
                className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                value={projB.coordinates.lng}
                onChange={e => setProjB({ ...projB, coordinates: { ...projB.coordinates, lng: parseFloat(e.target.value) || 0 } })}
              />
            </div>
          </div>
        </div>

      </div>

      {/* Action Button */}
      <div className="text-center">
        <button
          onClick={handleRunAiComparison}
          disabled={loading}
          className="px-8 py-4 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-black text-sm rounded-2xl shadow-xl shadow-orange-500/20 flex items-center space-x-3 mx-auto transition-all transform hover:-translate-y-0.5"
        >
          {loading ? (
            <RefreshCw className="h-5 w-5 animate-spin" />
          ) : (
            <Sparkles className="h-5 w-5" />
          )}
          <span>Run AI Similarity Analysis</span>
        </button>
      </div>

      {/* Results Display */}
      {result && (
        <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-xl space-y-6 animate-in fade-in duration-300">
          
          <div className="bg-slate-900 text-white rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                Live AI Output Result
              </span>
              <p className="text-base font-extrabold text-slate-100">
                {result.explanation}
              </p>
            </div>

            <div className="text-right shrink-0">
              <div className="text-3xl font-black text-amber-400">
                {result.similarity_percentage}%
              </div>
              <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">
                {result.risk_level} Risk Tier
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-slate-500 block mb-1 font-semibold">Text Similarity</span>
              <span className="text-xl font-bold text-blue-600">{result.score_breakdown.text_similarity_percentage}%</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-slate-500 block mb-1 font-semibold">Location Proximity</span>
              <span className="text-xl font-bold text-emerald-600">{result.score_breakdown.location_proximity_percentage}%</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-slate-500 block mb-1 font-semibold">Spatial Distance</span>
              <span className="text-xl font-bold text-slate-900">{result.score_breakdown.distance_meters} meters</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-slate-500 block mb-1 font-semibold">Time Window Overlap</span>
              <span className="text-xl font-bold text-amber-600">{Math.round(result.score_breakdown.time_overlap * 100)}%</span>
            </div>
          </div>

          <GeoDistanceMap
            projA={projA}
            projB={projB}
            distanceMeters={result.score_breakdown.distance_meters}
            proximityScore={result.score_breakdown.location_proximity}
          />

        </div>
      )}
    </div>
  );
}
