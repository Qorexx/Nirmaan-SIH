'use client';

import React from 'react';
import { MapPin, Navigation, Compass, ShieldAlert } from 'lucide-react';

export default function GeoDistanceMap({ projA, projB, distanceMeters, proximityScore }) {
  const lat1 = projA.coordinates?.lat || 25.3176;
  const lng1 = projA.coordinates?.lng || 82.9739;
  const lat2 = projB.coordinates?.lat || 25.3180;
  const lng2 = projB.coordinates?.lng || 82.9741;

  const centerLat = ((lat1 + lat2) / 2).toFixed(4);
  const centerLng = ((lng1 + lng2) / 2).toFixed(4);

  return (
    <div className="bg-slate-900 text-white rounded-2xl p-6 border border-slate-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <MapPin className="h-5 w-5 text-amber-400" />
          <h3 className="text-sm font-bold tracking-wide uppercase text-slate-200">
            Spatial Distance & Proximity Analysis
          </h3>
        </div>
        <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-bold px-3 py-1 rounded-lg flex items-center gap-1.5">
          <Navigation className="h-3.5 w-3.5" />
          Distance: {distanceMeters !== Infinity ? `${distanceMeters} meters` : 'N/A'}
        </span>
      </div>

      <div className="relative bg-slate-950 rounded-xl p-6 border border-slate-800 overflow-hidden min-h-[200px] flex flex-col justify-between">
        
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:16px_16px]"></div>

        <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-4">
          
          <div className="bg-slate-900/90 p-3.5 rounded-lg border border-blue-500/40 flex items-start space-x-3">
            <div className="h-9 w-9 rounded-lg bg-blue-500/20 border border-blue-400 flex items-center justify-center shrink-0">
              <span className="font-extrabold text-blue-400 text-sm">A</span>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 block mb-0.5">
                {projA.id}
              </span>
              <p className="text-xs font-semibold text-slate-200 line-clamp-1">{projA.title}</p>
              <div className="text-[11px] text-slate-400 font-mono mt-1">
                Lat: {lat1}, Lng: {lng1}
              </div>
            </div>
          </div>

          <div className="bg-slate-900/90 p-3.5 rounded-lg border border-indigo-500/40 flex items-start space-x-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-500/20 border border-indigo-400 flex items-center justify-center shrink-0">
              <span className="font-extrabold text-indigo-400 text-sm">B</span>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 block mb-0.5">
                {projB.id}
              </span>
              <p className="text-xs font-semibold text-slate-200 line-clamp-1">{projB.title}</p>
              <div className="text-[11px] text-slate-400 font-mono mt-1">
                Lat: {lat2}, Lng: {lng2}
              </div>
            </div>
          </div>

        </div>

        <div className="relative z-10 mt-6 pt-4 border-t border-slate-800 flex items-center justify-between">
          <div className="text-xs text-slate-400 flex items-center space-x-2">
            <Compass className="h-4 w-4 text-amber-400" />
            <span>Center Lat/Lng: <strong className="text-slate-200 font-mono">{centerLat}, {centerLng}</strong></span>
          </div>

          <div className="text-xs font-bold text-amber-400 flex items-center space-x-1.5 bg-amber-500/10 px-3 py-1 rounded-md border border-amber-500/20">
            <ShieldAlert className="h-3.5 w-3.5" />
            <span>Location Similarity: {Math.round(proximityScore * 100)}%</span>
          </div>
        </div>

      </div>
    </div>
  );
}
