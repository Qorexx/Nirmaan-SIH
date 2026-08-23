import { NextResponse } from 'next/server';
import { sampleProjects } from '../../../lib/sampleProjects';
import { findDuplicateProjects } from '../../../lib/duplicateEngine';

const DUPLICATE_AI_URL = process.env.DUPLICATE_AI_URL || 'http://localhost:8000';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const thresholdParam = searchParams.get('threshold');
  const threshold = thresholdParam ? parseFloat(thresholdParam) : 40.0;

  // ── Try Python ML service first ──────────────────────────────────────────
  try {
    const pyRes = await fetch(`${DUPLICATE_AI_URL}/find-duplicates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ projects: sampleProjects, threshold }),
      signal: AbortSignal.timeout(30000), // 30s timeout (model inference)
    });

    if (pyRes.ok) {
      const data = await pyRes.json();
      return NextResponse.json({
        ...data,
        _engine: 'python-ml',
        _model: 'paraphrase-multilingual-MiniLM-L12-v2',
      });
    }
  } catch (err) {
    console.warn('[find-duplicates] Python ML service unavailable, using JS fallback:', err.message);
  }

  // ── JS heuristic fallback (when Python service is offline) ───────────────
  const minThreshold = threshold / 100;
  const duplicatePairs = findDuplicateProjects(sampleProjects, minThreshold);
  const criticalCount = duplicatePairs.filter(p => p.risk_level === 'CRITICAL').length;
  const highCount = duplicatePairs.filter(p => p.risk_level === 'HIGH').length;

  return NextResponse.json({
    status: 'success',
    module: 'MPLADS Duplicate & Similarity Detection AI Engine',
    total_projects_scanned: sampleProjects.length,
    flagged_pairs_count: duplicatePairs.length,
    summary: {
      critical_duplicates: criticalCount,
      high_risk_overlaps: highCount,
      total_flagged: duplicatePairs.length,
    },
    results: duplicatePairs,
    _engine: 'js-heuristic-fallback',
    _warning: 'Python ML service offline. Start duplicate-ml service for real AI results.',
  });
}
