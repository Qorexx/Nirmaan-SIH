import { NextResponse } from 'next/server';
import { sampleProjects } from '../../lib/sampleProjects';
import { findDuplicateProjects } from '../../lib/duplicateEngine';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const thresholdParam = searchParams.get('threshold');
  const minThreshold = thresholdParam ? parseFloat(thresholdParam) : 0.40;

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
      total_flagged: duplicatePairs.length
    },
    results: duplicatePairs
  });
}
