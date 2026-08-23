import React from 'react';
import { MapPin, Calendar, Tag, ArrowRight, AlertTriangle, CheckCircle2, ChevronRight } from 'lucide-react';

export default function DuplicateCard({ pair, onInspect }) {
  const {
    duplicate_probability,
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
    <div className={`bg-white rounded-2xl border transition-all duration-200 hover:shadow-xl ${
      isCritical
        ? 'border-red-300 shadow-md shadow-red-500/5'
        : isHigh
        ? 'border-orange-300 shadow-md shadow-orange-500/5'
        : 'border-slate-200'
    }`}>
      {/* Card Header */}
      <div className={`px-6 py-4 rounded-t-2xl border-b flex flex-wrap items-center justify-between gap-3 ${
        isCritical
          ? 'bg-red-50/70 border-red-100'
          : isHigh
          ? 'bg-amber-50/70 border-amber-100'
          : 'bg-slate-50 border-slate-100'
      }`}>
        <div className="flex items-center space-x-3">
          <span className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wide flex items-center gap-1.5 ${
            isCritical
              ? 'bg-red-600 text-white shadow-sm'
              : isHigh
              ? 'bg-amber-500 text-slate-950 shadow-sm'
              : 'bg-slate-700 text-white'
          }`}>
            <AlertTriangle className="h-3.5 w-3.5" />
            {risk_badge} — {similarity_percentage}% similarity
          </span>
          <span className="text-xs text-slate-500 font-mono font-medium">ID: {pair.pair_id}</span>
        </div>

        <div className="text-xs font-semibold text-slate-600 bg-white px-3 py-1 rounded-lg border border-slate-200 shadow-2xs">
          District: <span className="text-slate-900 font-bold">{project_a.district}</span> ({project_a.state})
        </div>
      </div>

      {/* AI Explanation Banner */}
      <div className="px-6 py-3 bg-slate-900 text-slate-200 text-xs font-mono border-b border-slate-800 flex items-start space-x-2">
        <span className="text-amber-400 font-bold shrink-0">AI Output:</span>
        <p className="leading-relaxed text-slate-300">{explanation}</p>
      </div>

      {/* Side-by-Side Comparison Snippets */}
      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Project A */}
        <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                Project A ({project_a.id})
              </span>
              <span className="text-xs font-semibold text-slate-600">₹{(project_a.sanction_amount / 100000).toFixed(2)} Lakhs</span>
            </div>
            <h4 className="text-sm font-bold text-slate-900 mb-1 leading-snug">{project_a.title}</h4>
            <p className="text-xs text-slate-600 line-clamp-2 mb-3 leading-relaxed">{project_a.description}</p>
          </div>

          <div className="space-y-1.5 text-[11px] text-slate-500 border-t border-slate-200/60 pt-2.5">
            <div className="flex items-center space-x-1.5">
              <Tag className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>{project_a.category}</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>({project_a.coordinates.lat}, {project_a.coordinates.lng})</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>{project_a.execution_start} to {project_a.execution_end}</span>
            </div>
          </div>
        </div>

        {/* Project B */}
        <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                Project B ({project_b.id})
              </span>
              <span className="text-xs font-semibold text-slate-600">₹{(project_b.sanction_amount / 100000).toFixed(2)} Lakhs</span>
            </div>
            <h4 className="text-sm font-bold text-slate-900 mb-1 leading-snug">{project_b.title}</h4>
            <p className="text-xs text-slate-600 line-clamp-2 mb-3 leading-relaxed">{project_b.description}</p>
          </div>

          <div className="space-y-1.5 text-[11px] text-slate-500 border-t border-slate-200/60 pt-2.5">
            <div className="flex items-center space-x-1.5">
              <Tag className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>{project_b.category}</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>({project_b.coordinates.lat}, {project_b.coordinates.lng})</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>{project_b.execution_start} to {project_b.execution_end}</span>
            </div>
          </div>
        </div>

      </div>

      {/* Multi-Factor Score Bars */}
      <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4">
        
        <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-slate-500 block mb-1 font-medium">Text Similarity</span>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${score_breakdown.text_similarity_percentage}%` }}></div>
              </div>
              <span className="font-bold text-slate-800">{score_breakdown.text_similarity_percentage}%</span>
            </div>
          </div>

          <div>
            <span className="text-slate-500 block mb-1 font-medium">Location Proximity</span>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden">
                <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${score_breakdown.location_proximity_percentage}%` }}></div>
              </div>
              <span className="font-bold text-slate-800">{score_breakdown.location_proximity_percentage}%</span>
            </div>
          </div>

          <div>
            <span className="text-slate-500 block mb-1 font-medium">Distance</span>
            <span className="font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200 inline-block">
              {score_breakdown.distance_meters !== Infinity ? `${score_breakdown.distance_meters}m apart` : 'N/A'}
            </span>
          </div>

          <div>
            <span className="text-slate-500 block mb-1 font-medium">Category</span>
            <span className="font-semibold text-emerald-700 flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {score_breakdown.category_match >= 0.9 ? 'Same Sector' : 'Related'}
            </span>
          </div>
        </div>

        <button
          onClick={() => onInspect(pair)}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl flex items-center space-x-1.5 transition-all shadow-sm hover:shadow shrink-0"
        >
          <span>Inspect AI Breakdown</span>
          <ChevronRight className="h-4 w-4" />
        </button>

      </div>
    </div>
  );
}
