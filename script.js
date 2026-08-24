// NIRMAAN MPLADS PLATFORM - Static Frontend Script

const MOCK_PROJECTS = {
  'PROJ-999': {
    id: 'PROJ-999',
    name: 'Community Hall Construction & Water Supply (High Risk Sample)',
    location: { lat: 28.6139, lng: 77.2090 },
    status: 'CRITICAL_ALERT',
    blockchainVerified: true,
    alerts: [
      {
        type: 'DUPLICATE_SUSPICION',
        message: 'Proposal is 92.5% similar to past project PROJ-2022-001 (Shared keywords: water_treatment, community_hall).',
        severity: 'CRITICAL'
      },
      {
        type: 'FINANCIAL_DEVIATION',
        message: 'Financial anomaly detected. Key drivers: expenditure_velocity_3x_normal. Variance: ₹1,500,000.00',
        severity: 'HIGH'
      },
      {
        type: 'COST_OVERRUN_WARNING',
        message: 'Predicted cost overrun of ₹500,000.00 based on contractor history.',
        severity: 'HIGH'
      },
      {
        type: 'PREDICTIVE_WARNING',
        message: 'Project forecasted to be delayed by 45 days due to: contractor_historical_delay.',
        severity: 'MEDIUM'
      }
    ]
  },
  'PROJ-101': {
    id: 'PROJ-101',
    name: 'Rural Solar Street Lighting Installation (On Track Sample)',
    location: { lat: 26.9124, lng: 75.7873 },
    status: 'ON_TRACK',
    blockchainVerified: true,
    alerts: []
  }
};

// Handle Search Form Submission on Index
document.addEventListener('DOMContentLoaded', () => {
  const searchForm = document.getElementById('search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const inputVal = document.getElementById('project-id-input').value.trim() || 'PROJ-999';
      window.location.href = `dashboard.html?id=${encodeURIComponent(inputVal)}`;
    });
  }

  // Auto-populate dashboard page if on dashboard.html
  if (window.location.pathname.includes('dashboard.html')) {
    loadProjectData();
  }
});

function quickLoad(id) {
  window.location.href = `dashboard.html?id=${encodeURIComponent(id)}`;
}

function loadProjectData() {
  const urlParams = new URLSearchParams(window.location.search);
  const projectId = urlParams.get('id') || 'PROJ-999';

  const data = MOCK_PROJECTS[projectId] || {
    id: projectId,
    name: `Custom Project (${projectId})`,
    location: { lat: 28.6139, lng: 77.2090 },
    status: 'NEEDS_ATTENTION',
    blockchainVerified: true,
    alerts: [
      {
        type: 'UNVERIFIED_INVOICE',
        message: 'Invoice submitted without EXIF metadata verification.',
        severity: 'MEDIUM'
      }
    ]
  };

  // Populate Dashboard UI elements
  const elId = document.getElementById('display-project-id');
  const elName = document.getElementById('display-project-name');
  const elLoc = document.getElementById('display-project-loc');
  const elCoords = document.getElementById('display-coords');
  const elStatus = document.getElementById('display-status-badge');
  const elAlerts = document.getElementById('alerts-container');

  if (elId) elId.textContent = `Project ID: ${data.id}`;
  if (elName) elName.textContent = data.name;
  if (elLoc) elLoc.textContent = `Location: Lat ${data.location.lat}, Lng ${data.location.lng} | Category: Infrastructure`;
  if (elCoords) elCoords.textContent = `Target Coordinates: (${data.location.lat}, ${data.location.lng})`;

  if (elStatus) {
    elStatus.textContent = `STATUS: ${data.status}`;
    elStatus.className = `badge ${getStatusClass(data.status)}`;
  }

  if (elAlerts) {
    if (data.alerts.length === 0) {
      elAlerts.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: var(--status-on-track);">
          No compliance violations detected. Project is on track.
        </div>
      `;
    } else {
      elAlerts.innerHTML = data.alerts.map(a => `
        <div class="alert-item severity-${a.severity}">
          <div>
            <strong>[${a.type}]</strong>
            <p style="font-size: 0.9rem; margin-top: 0.25rem;">${a.message}</p>
          </div>
          <span class="badge badge-${a.severity.toLowerCase()}">${a.severity}</span>
        </div>
      `).join('');
    }
  }
}

function getStatusClass(status) {
  switch (status) {
    case 'CRITICAL_ALERT': return 'badge-critical';
    case 'HIGH_RISK': return 'badge-high';
    case 'NEEDS_ATTENTION': return 'badge-medium';
    case 'ON_TRACK': return 'badge-on-track';
    default: return 'badge-secondary';
  }
}

function handleAction(actionName) {
  const toast = document.getElementById('notification-box');
  if (toast) {
    toast.textContent = `Action Triggered: ${actionName}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 4000);
  }
}
