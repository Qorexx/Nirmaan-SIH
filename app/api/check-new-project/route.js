import { NextResponse } from 'next/server';
import { sampleProjects } from '../../../lib/sampleProjects';
import { compareProjectPair } from '../../../lib/duplicateEngine';

const DUPLICATE_AI_URL = process.env.DUPLICATE_AI_URL || 'http://localhost:8000';

export async function POST(request) {
  try {
    const newProject = await request.json();

    if (!newProject || !newProject.title) {
      return NextResponse.json(
        { status: 'error', message: 'Missing required project payload (title, coordinates, category)' },
        { status: 400 }
      );
    }

    // ── Try Python ML service first ──────────────────────────────────────────
    try {
      const pyRes = await fetch(`${DUPLICATE_AI_URL}/check-new-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_project: newProject,
          existing_projects: sampleProjects,
          threshold: 40.0,
        }),
        signal: AbortSignal.timeout(30000),
      });

      if (pyRes.ok) {
        const data = await pyRes.json();
        return NextResponse.json({
          ...data,
          _engine: 'python-ml',
        });
      }
    } catch (err) {
      console.warn('[check-new-project] Python ML service unavailable, using JS fallback:', err.message);
    }

    // ── JS heuristic fallback ────────────────────────────────────────────────
    const candidateMatches = [];

    for (const existingProj of sampleProjects) {
      const analysis = compareProjectPair(newProject, existingProj);
      if (analysis.duplicate_probability >= 0.40) {
        candidateMatches.push(analysis);
      }
    }

    candidateMatches.sort((a, b) => b.duplicate_probability - a.duplicate_probability);

    const highestRisk = candidateMatches[0] || null;
    const isDuplicateFlagged = highestRisk && highestRisk.duplicate_probability >= 0.70;

    return NextResponse.json({
      status: 'success',
      is_duplicate_flagged: isDuplicateFlagged,
      highest_risk_score: highestRisk ? highestRisk.duplicate_probability : 0,
      recommendation: isDuplicateFlagged
        ? '🔴 REJECT/HOLD: High duplicate probability detected with existing sanctioned project.'
        : '🟢 CLEAR: Low probability of duplicate work.',
      top_matches: candidateMatches.slice(0, 5),
      _engine: 'js-heuristic-fallback',
      _warning: 'Python ML service offline. Scores are heuristic estimates.',
    });
  } catch (err) {
    return NextResponse.json({ status: 'error', message: err.message }, { status: 500 });
  }
}
