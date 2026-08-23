import { NextResponse } from 'next/server';
import { compareProjectPair } from '../../../lib/duplicateEngine';

const DUPLICATE_AI_URL = process.env.DUPLICATE_AI_URL || 'http://localhost:8000';

/**
 * Adapter: maps Python ML service output → frontend-expected field names.
 * The Python service uses `potential_duplicate_score` as the canonical name.
 * The frontend (SandboxTester, DuplicateCard, ComparisonModal) reads:
 *   similarity_percentage, risk_level, risk_badge, score_breakdown, project_a, project_b
 * These are all already present in the Python output — this adapter just normalises
 * any differences and ensures backward compatibility.
 */
function adaptPythonAnalysis(pyAnalysis) {
  return {
    pair_id:                   pyAnalysis.pair_id,
    potential_duplicate_score: pyAnalysis.potential_duplicate_score,
    similarity_percentage:     pyAnalysis.similarity_percentage ?? pyAnalysis.potential_duplicate_score,
    duplicate_probability:     pyAnalysis.duplicate_probability,
    risk_level:                pyAnalysis.risk_level,
    risk_badge:                pyAnalysis.risk_badge,
    explanation:               pyAnalysis.explanation,
    reasons:                   pyAnalysis.reasons ?? [],
    score_breakdown:           pyAnalysis.score_breakdown,
    project_a:                 pyAnalysis.project_a,
    project_b:                 pyAnalysis.project_b,
    metadata:                  pyAnalysis.metadata ?? {},
    _engine:                   'python-ml',
    _model:                    'paraphrase-multilingual-MiniLM-L12-v2',
  };
}

export async function POST(request) {
  try {
    const { projectA, projectB } = await request.json();

    if (!projectA || !projectB) {
      return NextResponse.json(
        { status: 'error', message: 'Must provide projectA and projectB in request body' },
        { status: 400 }
      );
    }

    // ── Try Python ML service first ────────────────────────────────────────
    try {
      const pyRes = await fetch(`${DUPLICATE_AI_URL}/compare-pair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectA, projectB }),
        signal: AbortSignal.timeout(30000),
      });

      if (pyRes.ok) {
        const data = await pyRes.json();
        return NextResponse.json({
          status: 'success',
          analysis: adaptPythonAnalysis(data.analysis),
        });
      }
    } catch (err) {
      console.warn('[compare-pair] Python ML service unavailable, using JS fallback:', err.message);
    }

    // ── JS heuristic fallback ──────────────────────────────────────────────
    const analysis = compareProjectPair(projectA, projectB);
    return NextResponse.json({
      status: 'success',
      analysis: {
        ...analysis,
        _engine: 'js-heuristic-fallback',
        _warning: 'Python ML service offline. Scores are heuristic estimates.',
      },
    });
  } catch (err) {
    return NextResponse.json({ status: 'error', message: err.message }, { status: 500 });
  }
}
