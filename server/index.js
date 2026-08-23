import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { compareProjectPair, findDuplicateProjects } from './services/duplicateEngine.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Load sample projects dataset
const sampleProjectsPath = path.join(__dirname, 'data', 'sampleProjects.json');
let projects = [];

try {
  const data = fs.readFileSync(sampleProjectsPath, 'utf8');
  projects = JSON.parse(data);
  console.log(`[MPLADS AI] Loaded ${projects.length} sample projects successfully.`);
} catch (err) {
  console.error('[MPLADS AI] Error reading sample projects dataset:', err);
}

// GET /api/health - Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'online',
    module: 'Person 3 — Duplicate & Similarity Detection AI',
    version: '1.0.0',
    total_projects: projects.length,
    timestamp: new Date().toISOString()
  });
});

// GET /api/projects - List all projects
app.get('/api/projects', (req, res) => {
  res.json({
    status: 'success',
    count: projects.length,
    projects
  });
});

// GET /find-duplicates or /api/find-duplicates
// Main deliverable required for Person 6's Risk Engine
app.get(['/find-duplicates', '/api/find-duplicates'], (req, res) => {
  const minThreshold = req.query.threshold ? parseFloat(req.query.threshold) : 0.40;
  const duplicatePairs = findDuplicateProjects(projects, minThreshold);

  const criticalCount = duplicatePairs.filter(p => p.risk_level === 'CRITICAL').length;
  const highCount = duplicatePairs.filter(p => p.risk_level === 'HIGH').length;

  res.json({
    status: 'success',
    module: 'Person 3 — Duplicate & Similarity Detection AI',
    total_projects_scanned: projects.length,
    flagged_pairs_count: duplicatePairs.length,
    summary: {
      critical_duplicates: criticalCount,
      high_risk_overlaps: highCount,
      total_flagged: duplicatePairs.length
    },
    results: duplicatePairs
  });
});

// POST /api/check-new-project
// Check a newly proposed project against existing projects to block duplicate sanctioning
app.post('/api/check-new-project', (req, res) => {
  const newProject = req.body;

  if (!newProject || !newProject.title) {
    return res.status(400).json({ status: 'error', message: 'Missing required project payload (title, coordinates, category)' });
  }

  const candidateMatches = [];

  for (const existingProj of projects) {
    const analysis = compareProjectPair(newProject, existingProj);
    if (analysis.duplicate_probability >= 0.40) {
      candidateMatches.push(analysis);
    }
  }

  candidateMatches.sort((a, b) => b.duplicate_probability - a.duplicate_probability);

  const highestRisk = candidateMatches[0] || null;
  const isDuplicateFlagged = highestRisk && highestRisk.duplicate_probability >= 0.70;

  res.json({
    status: 'success',
    is_duplicate_flagged: isDuplicateFlagged,
    highest_risk_score: highestRisk ? highestRisk.duplicate_probability : 0,
    recommendation: isDuplicateFlagged
      ? '🔴 REJECT/HOLD: High duplicate probability detected with existing sanctioned project.'
      : '🟢 CLEAR: Low probability of duplicate work.',
    top_matches: candidateMatches.slice(0, 5)
  });
});

// POST /api/compare-pair
// Compare any 2 custom project objects live (used for interactive sandbox)
app.post('/api/compare-pair', (req, res) => {
  const { projectA, projectB } = req.body;

  if (!projectA || !projectB) {
    return res.status(400).json({ status: 'error', message: 'Must provide projectA and projectB in request body' });
  }

  const analysis = compareProjectPair(projectA, projectB);
  res.json({
    status: 'success',
    analysis
  });
});

app.listen(PORT, () => {
  console.log(`\n======================================================`);
  console.log(`  Person 3 — Duplicate & Similarity Detection AI Server`);
  console.log(`  Running on http://localhost:${PORT}`);
  console.log(`  Deliverable API: http://localhost:${PORT}/find-duplicates`);
  console.log(`======================================================\n`);
});
