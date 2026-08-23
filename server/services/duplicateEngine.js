/**
 * Person 3 — Duplicate & Similarity Detection Engine (Server JS Fallback)
 * 
 * Clean multi-factor math engine.
 * NO HARDCODED values (no 0.91, no 0.85 timeScore, no 0.93 probability).
 */

const STOP_WORDS = new Set([
  'a', 'an', 'the', 'in', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
  'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
  'to', 'from', 'up', 'upon', 'down', 'out', 'on', 'off', 'over', 'under',
  'and', 'or', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
  'work', 'project', 'scheme', 'mplad', 'mplads', 'near', 'ward'
]);

function tokenize(text) {
  if (!text) return [];
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(word => word.length > 1 && !STOP_WORDS.has(word));
}

export function calculateTextSimilarity(text1, text2) {
  const tokens1 = tokenize(text1);
  const tokens2 = tokenize(text2);

  if (tokens1.length === 0 || tokens2.length === 0) return 0;

  const set1 = new Set(tokens1);
  const set2 = new Set(tokens2);

  const intersection = new Set([...set1].filter(x => set2.has(x)));
  const union = new Set([...set1, ...set2]);

  return union.size > 0 ? intersection.size / union.size : 0;
}

export function calculateHaversineDistance(lat1, lon1, lat2, lon2) {
  if (lat1 === undefined || lon1 === undefined || lat2 === undefined || lon2 === undefined ||
      lat1 === null || lon1 === null || lat2 === null || lon2 === null) {
    return null;
  }

  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c * 10) / 10;
}

export function calculateLocationProximityScore(distanceMeters) {
  if (distanceMeters === null || distanceMeters === undefined) return null;
  if (distanceMeters <= 10) return 1.0;
  if (distanceMeters <= 100) return Math.max(0.80, 0.98 * Math.exp(-0.002 * (distanceMeters - 10)));
  if (distanceMeters <= 500) return Math.max(0.40, 0.80 * Math.exp(-0.0017 * (distanceMeters - 100)));
  if (distanceMeters <= 2000) return Math.max(0.0, 0.40 * (1 - (distanceMeters - 500) / 1500));
  return 0.0;
}

export function calculateTemporalOverlap(startA, endA, startB, endB) {
  if (!startA || !startB) return null;

  const sa = new Date(startA).getTime();
  const ea = endA ? new Date(endA).getTime() : sa;
  const sb = new Date(startB).getTime();
  const eb = endB ? new Date(endB).getTime() : sb;

  if (isNaN(sa) || isNaN(sb)) return null;

  const overlapStart = Math.max(sa, sb);
  const overlapEnd = Math.min(ea, eb);
  const overlapMs = Math.max(0, overlapEnd - overlapStart);

  const unionStart = Math.min(sa, sb);
  const unionEnd = Math.max(ea, eb);
  const unionMs = unionEnd - unionStart;

  if (unionMs === 0) return 1.0;
  return overlapMs / unionMs;
}

export function compareProjectPair(projA, projB) {
  const textScore = calculateTextSimilarity(
    `${projA.title} ${projA.description || ''}`,
    `${projB.title} ${projB.description || ''}`
  );

  const latA = projA.latitude ?? projA.coordinates?.lat;
  const lonA = projA.longitude ?? projA.coordinates?.lng;
  const latB = projB.latitude ?? projB.coordinates?.lat;
  const lonB = projB.longitude ?? projB.coordinates?.lng;

  const distMeters = calculateHaversineDistance(latA, lonA, latB, lonB);
  const geoScore = calculateLocationProximityScore(distMeters);

  const catScore = projA.category && projB.category
    ? (projA.category.toLowerCase() === projB.category.toLowerCase() ? 1.0 : 0.4)
    : null;

  const timeScore = calculateTemporalOverlap(
    projA.execution_start, projA.execution_end,
    projB.execution_start, projB.execution_end
  );

  const baseWeights = { text: 0.50, location: 0.25, category: 0.15, temporal: 0.10 };
  const signals = { text: textScore, location: geoScore, category: catScore, temporal: timeScore };

  let availableWeightSum = 0;
  Object.keys(signals).forEach(k => {
    if (signals[k] !== null) availableWeightSum += baseWeights[k];
  });

  let rawScore = 0;
  if (availableWeightSum > 0) {
    Object.keys(signals).forEach(k => {
      if (signals[k] !== null) {
        rawScore += (baseWeights[k] / availableWeightSum) * signals[k];
      }
    });
  }

  const finalScorePercent = Math.round(rawScore * 100);

  let riskLevel = 'LOW';
  let riskBadge = '🟢 Low Similarity';

  if (finalScorePercent >= 90) {
    riskLevel = 'CRITICAL REVIEW';
    riskBadge = '🔴 Critical Duplicate Risk';
  } else if (finalScorePercent >= 75) {
    riskLevel = 'VERY HIGH';
    riskBadge = '🟠 Very High Overlap Risk';
  } else if (finalScorePercent >= 60) {
    riskLevel = 'HIGH';
    riskBadge = '🟠 High Risk Overlap';
  } else if (finalScorePercent >= 40) {
    riskLevel = 'MODERATE';
    riskBadge = '🟡 Moderate Similarity';
  }

  const textPercent = Math.round(textScore * 100);
  const geoPercent = geoScore !== null ? Math.round(geoScore * 100) : null;
  const distText = distMeters !== null ? `${distMeters}m apart` : 'location unspecified';
  const timeText = timeScore !== null ? `${Math.round(timeScore * 100)}% execution overlap` : 'execution dates unspecified';

  const explanation = `${riskBadge} — ${finalScorePercent}% Potential Duplicate Score. ` +
    `Description similarity: ${textPercent}% | Location proximity: ${geoPercent !== null ? geoPercent + '%' : 'N/A'} (${distText}) | ${timeText}.`;

  return {
    pair_id: `DUP-${projA.id}-${projB.id}`,
    potential_duplicate_score: finalScorePercent,
    similarity_percentage: finalScorePercent,
    duplicate_probability: Math.round(rawScore * 100) / 100,
    risk_level: riskLevel,
    risk_badge: riskBadge,
    explanation,
    score_breakdown: {
      text_similarity: Math.round(textScore * 10000) / 10000,
      text_similarity_percentage: textPercent,
      location_proximity: geoScore !== null ? Math.round(geoScore * 10000) / 10000 : null,
      location_proximity_percentage: geoPercent,
      distance_meters: distMeters,
      category_match: catScore,
      time_overlap: timeScore !== null ? Math.round(timeScore * 10000) / 10000 : null
    },
    project_a: projA,
    project_b: projB
  };
}

export function findDuplicateProjects(projects, threshold = 40.0) {
  const minScore = threshold > 1 ? threshold : threshold * 100;
  const flaggedPairs = [];

  for (let i = 0; i < projects.length; i++) {
    for (let j = i + 1; j < projects.length; j++) {
      const projA = projects[i];
      const projB = projects[j];

      if (projA.district && projB.district && projA.district !== projB.district) {
        continue;
      }

      const analysis = compareProjectPair(projA, projB);

      if (analysis.potential_duplicate_score >= minScore) {
        flaggedPairs.push(analysis);
      }
    }
  }

  return flaggedPairs.sort((a, b) => b.potential_duplicate_score - a.potential_duplicate_score);
}
