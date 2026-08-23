'use client';

import React from 'react';
import { X, AlertTriangle, Building2 } from 'lucide-react';
import GeoDistanceMap from './GeoDistanceMap';

export default function ComparisonModal({ pair, onClose }) {
  if (!pair) return null;

  const {
    similarity_percentage,
    risk_level,
    risk_badge,
    explanation,
    score_breakdown,
    project_a,
    project_b
  } = pair;

  const isCritical = risk_level === 'CRITICAL';
  const isHigh = risk_level === 'HIGH';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-5xl w-full shadow-2xl overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="bg-slate-900 text-white px-8 py-6 flex items-center justify-between border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${
                isCritical ? 'bg-red-600 text-white' : isHigh ? 'bg-amber-500 text-slate-950' : 'bg-slate-700 text-white'
              }`}>
                {risk_badge} — {similarity_percentage}% Duplicate Score
              </span>
              <span className="text-xs text-slate-400 font-mono">ID: {pair.pair_id}</span>
            </div>
            <h2 className="text-xl font-extrabold text-slate-100">
              AI Duplicate & Similarity Deep Inspection
            </h2>
          </div>

          <button
            onClick={onClose}
            className="h-10 w-10 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center justify-center transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-8 space-y-8 max-h-[80vh] overflow-y-auto">
          
          {/* AI Output Banner */}
          <div className="bg-gradient-to-r from-red-950 via-slate-900 to-slate-900 text-white rounded-2xl p-6 border border-red-900/60 shadow-lg">
            <div className="flex items-start space-x-3">
              <div className="h-10 w-10 rounded-xl bg-red-600/30 border border-red-500/50 flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
              <div className="space-y-2">
                <div className="text-xs font-bold uppercase tracking-wider text-red-400">
                  Official AI Detection Output
                </div>
                <p className="text-base font-bold text-slate-100 leading-snug">
                  {explanation}
                </p>
                <div className="text-xs text-slate-400 pt-1 font-mono">
                  This structured finding is automatically exported into the risk engine scoring pipeline.
                </div>
              </div>
            </div>
          </div>

          {/* Factor Breakdown Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
              <span className="text-xs text-slate-500 font-semibold block mb-1">Description Similarity</span>
              <div className="text-2xl font-black text-blue-600">{score_breakdown.text_similarity_percentage}%</div>
              <span className="text-[11px] text-slate-400 mt-1 block">NLP Vector Embedding</span>
            </div>

            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
              <span className="text-xs text-slate-500 font-semibold block mb-1">Location Proximity</span>
              <div className="text-2xl font-black text-emerald-600">{score_breakdown.location_proximity_percentage}%</div>
              <span className="text-[11px] text-slate-400 mt-1 block">
                {score_breakdown.distance_meters !== Infinity ? `${score_breakdown.distance_meters}m apart` : 'N/A'}
              </span>
            </div>

            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
              <span className="text-xs text-slate-500 font-semibold block mb-1">Project Category</span>
              <div className="text-2xl font-black text-indigo-600">
                {score_breakdown.category_match >= 0.9 ? '100%' : '70%'}
              </div>
              <span className="text-[11px] text-slate-400 mt-1 block">Taxonomy Overlap</span>
            </div>

            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
              <span className="text-xs text-slate-500 font-semibold block mb-1">Execution Window</span>
              <div className="text-2xl font-black text-amber-600">
                {Math.round(score_breakdown.time_overlap * 100)}%
              </div>
              <span className="text-[11px] text-slate-400 mt-1 block">Timeline Overlap</span>
            </div>
          </div>

          {/* Side-by-Side Detailed Comparison */}
          <div>
            <h3 className="text-base font-extrabold text-slate-900 mb-4 flex items-center gap-2">
              <Building2 className="h-5 w-5 text-slate-700" />
              Side-by-Side Project Details
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Project A */}
              <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <span className="bg-blue-600 text-white text-xs font-black px-3 py-1 rounded-lg">
                    Project A: {project_a.id}
                  </span>
                  <span className="text-sm font-black text-slate-900">
                    ₹{(project_a.sanction_amount / 100000).toFixed(2)} Lakhs
                  </span>
                </div>

                <div>
                  <h4 className="text-base font-extrabold text-slate-900 mb-2">{project_a.title}</h4>
                  <p className="text-xs text-slate-600 leading-relaxed bg-white p-3 rounded-xl border border-slate-200">
                    {project_a.description}
                  </p>
                </div>

                <div className="space-y-2 text-xs text-slate-600 font-medium">
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-400">Category</span>
                    <span className="font-bold text-slate-800">{project_a.category}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-400">Constituency</span>
                    <span className="font-bold text-slate-800">{project_a.constituency} ({project_a.district})</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-400">Implementing Agency</span>
                    <span className="font-bold text-slate-800">{project_a.implementing_agency}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Execution Window</span>
                    <span className="font-bold text-slate-800">{project_a.execution_start} to {project_a.execution_end}</span>
                  </div>
                </div>
              </div>

              {/* Project B */}
              <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <span className="bg-indigo-600 text-white text-xs font-black px-3 py-1 rounded-lg">
                    Project B: {project_b.id}
                  </span>
                  <span className="text-sm font-black text-slate-900">
                    ₹{(project_b.sanction_amount / 100000).toFixed(2)} Lakhs
                  </span>
                </div>

                <div>
                  <h4 className="text-base font-extrabold text-slate-900 mb-2">{project_b.title}</h4>
                  <p className="text-xs text-slate-600 leading-relaxed bg-white p-3 rounded-xl border border-slate-200">
                    {project_b.description}
                  </p>
                </div>

                <div className="space-y-2 text-xs text-slate-600 font-medium">
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-400">Category</span>
                    <span className="font-bold text-slate-800">{project_b.category}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-400">Constituency</span>
                    <span className="font-bold text-slate-800">{project_b.constituency} ({project_b.district})</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-400">Implementing Agency</span>
                    <span className="font-bold text-slate-800">{project_b.implementing_agency}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Execution Window</span>
                    <span className="font-bold text-slate-800">{project_b.execution_start} to {project_b.execution_end}</span>
                  </div>
                </div>
              </div>

            </div>
          </div>

          <GeoDistanceMap
            projA={project_a}
            projB={project_b}
            distanceMeters={score_breakdown.distance_meters}
            proximityScore={score_breakdown.location_proximity}
          />

        </div>

        {/* Modal Footer */}
        <div className="bg-slate-100 px-8 py-4 flex items-center justify-between border-t border-slate-200">
          <div className="text-xs text-slate-500 font-mono">
            Structured Risk Findings Export
          </div>
          <button
            onClick={onClose}
            className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl transition-all shadow"
          >
            Close Inspector
          </button>
        </div>

      </div>
    </div>
  );
}
