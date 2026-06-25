/**
 * MedCode AI Admin Dashboard — Vanilla JS
 * API prefix: /api/v19/dashboard/*
 */

const API_BASE = '/api/v19/dashboard';
const API_V19 = '/api/v19';

let currentPage = 1;
const PAGE_SIZE = 20;
let claimsFilters = { status: '', payer: '', date_from: '', date_to: '' };

// ── Utility ─────────────────────────────────────────────────────────────

function getToken() {
  return localStorage.getItem('medcode_token') || '';
}

function authHeaders() {
  const t = getToken();
  return t ? { 'Authorization': `Bearer ${t}` } : {};
}

async function apiFetch(url, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...authHeaders(), ...(opts.headers || {}) };
  try {
    const res = await fetch(url, { ...opts, headers });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/pdf')) return res.blob();
    return res.json();
  } catch (e) {
    showToast(e.message, 'error');
    throw e;
  }
}

function showToast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  while (c.children.length >= 5) c.removeChild(c.firstChild);
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3500);
}

function showLoading(el) {
  el.innerHTML = '<div class="flex items-center justify-center py-8"><span class="spinner"></span></div>';
}

function formatDate(d) {
  if (!d) return '—';
  const dt = new Date(d);
  return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function statusBadge(status) {
  const s = (status || '').toLowerCase();
  const cls = s === 'paid' ? 'badge-paid' : s === 'pending' ? 'badge-pending' : s === 'denied' ? 'badge-denied' : s === 'submitted' ? 'badge-submitted' : 'badge-draft';
  return `<span class="badge ${cls}">${status || 'Draft'}</span>`;
}

function fmtMoney(n) {
  return n != null ? '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2 }) : '—';
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

// ── Tab Navigation ──────────────────────────────────────────────────────

const tabs = ['overview', 'claims', 'coding', 'users', 'reports', 'settings'];
let activeTab = 'overview';

function switchTab(tab) {
  activeTab = tab;
  tabs.forEach(t => {
    document.getElementById('tab-btn-' + t)?.classList.toggle('active', t === tab);
    document.getElementById('section-' + t)?.classList.toggle('hidden', t !== tab);
  });
  if (tab === 'overview') loadOverview();
  else if (tab === 'claims') loadClaims();
  else if (tab === 'coding') loadCoding();
  else if (tab === 'users') loadUsers();
  else if (tab === 'reports') loadReports();
  else if (tab === 'settings') loadSettings();
}

// ── Overview Tab ────────────────────────────────────────────────────────

let statusChart = null, revenueChart = null;

async function loadOverview() {
  try {
    const stats = await apiFetch(`${API_BASE}/stats`);
    document.getElementById('stat-total-claims').textContent = (stats.total_claims ?? 0).toLocaleString();
    document.getElementById('stat-pending').textContent = (stats.pending_claims ?? 0).toLocaleString();
    document.getElementById('stat-paid').textContent = (stats.paid_claims ?? 0).toLocaleString();
    document.getElementById('stat-denied').textContent = (stats.denied_claims ?? 0).toLocaleString();
    document.getElementById('stat-revenue').textContent = fmtMoney(stats.total_revenue);
  } catch (e) { console.error('Failed to load overview stats:', e); }

  try {
    const charts = await apiFetch(`${API_BASE}/charts`);
    renderStatusChart(charts.by_status || {});
    renderRevenueChart(charts.revenue_trend || []);
  } catch (e) { console.error('Failed to load charts:', e); }

  try {
    const act = await apiFetch(`${API_BASE}/activity?limit=10`);
    renderActivity(act.events || []);
  } catch (e) { console.error('Failed to load activity:', e); }
}

function renderStatusChart(data) {
  const labels = Object.keys(data);
  const values = Object.values(data);
  const colors = ['#6366f1', '#22c55e', '#ef4444', '#f59e0b', '#6b7280', '#06b6d4'];
  if (statusChart) statusChart.destroy();
  statusChart = new Chart(document.getElementById('statusChart'), {
    type: 'doughnut',
    data: { labels, datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length) }] },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
  });
}

function renderRevenueChart(data) {
  const labels = data.map(d => d.date || d.label || '');
  const values = data.map(d => d.revenue || d.value || 0);
  if (revenueChart) revenueChart.destroy();
  revenueChart = new Chart(document.getElementById('revenueChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Revenue',
        data: values,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99,102,241,0.1)',
        fill: true,
        tension: 0.3,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + v.toLocaleString() } } }
    }
  });
}

function renderActivity(events) {
  const el = document.getElementById('activity-feed');
  if (!events.length) { el.innerHTML = '<p class="text-gray-400 text-sm py-4">No recent activity</p>'; return; }
  const dotColors = { created: 'bg-blue-500', submitted: 'bg-indigo-500', paid: 'bg-green-500', denied: 'bg-red-500', updated: 'bg-yellow-500' };
  el.innerHTML = events.map(e => {
    const color = dotColors[e.type] || 'bg-gray-400';
    return `<div class="activity-item">
      <span class="activity-dot ${color}"></span>
      <div>
        <p class="text-sm text-gray-800">${e.description || e.type}</p>
        <p class="text-xs text-gray-400 mt-0.5">${formatDate(e.timestamp)}</p>
      </div>
    </div>`;
  }).join('');
}

// ── Claims Tab ──────────────────────────────────────────────────────────

async function loadClaims() {
  showLoading(document.getElementById('claims-table-body'));
  const params = new URLSearchParams({ page: currentPage, limit: PAGE_SIZE });
  if (claimsFilters.status) params.set('status', claimsFilters.status);
  if (claimsFilters.payer) params.set('payer', claimsFilters.payer);
  if (claimsFilters.date_from) params.set('date_from', claimsFilters.date_from);
  if (claimsFilters.date_to) params.set('date_to', claimsFilters.date_to);

  try {
    const data = await apiFetch(`${API_V19}/billing/batches?${params}`);
    const claims = data.claims || [];
    const total = data.total || claims.length;
    renderClaimsTable(claims);
    renderPagination(total);
  } catch {
    document.getElementById('claims-table-body').innerHTML = '<tr><td colspan="7" class="text-center py-4 text-gray-400">No data</td></tr>';
  }
}

function renderClaimsTable(claims) {
  const tbody = document.getElementById('claims-table-body');
  if (!claims.length) { tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-gray-400">No claims found</td></tr>'; return; }
  tbody.innerHTML = claims.map(c => `<tr onclick="showClaimDetail('${escapeHtml(c.claim_id)}')">
    <td class="font-mono text-xs">${escapeHtml(c.claim_id) || '—'}</td>
    <td>${escapeHtml(c.patient_name) || 'REDACTED'}</td>
    <td>${escapeHtml(c.payer_name) || '—'}</td>
    <td>${fmtMoney(c.total_charges)}</td>
    <td>${statusBadge(c.status)}</td>
    <td>${formatDate(c.created_at)}</td>
    <td><button class="text-indigo-600 hover:text-indigo-800 text-xs font-medium" onclick="event.stopPropagation();showClaimDetail('${escapeHtml(c.claim_id)}')">View</button></td>
  </tr>`).join('');
}

function renderPagination(total) {
  const pages = Math.ceil(total / PAGE_SIZE);
  const el = document.getElementById('claims-pagination');
  if (pages <= 1) { el.innerHTML = ''; return; }
  let html = '';
  for (let i = 1; i <= pages && i <= 10; i++) {
    html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
  }
  el.innerHTML = html;
}

function goToPage(p) { currentPage = p; loadClaims(); }

function filterClaims() {
  claimsFilters.status = document.getElementById('filter-status').value;
  claimsFilters.payer = document.getElementById('filter-payer').value;
  claimsFilters.date_from = document.getElementById('filter-date-from').value;
  claimsFilters.date_to = document.getElementById('filter-date-to').value;
  currentPage = 1;
  loadClaims();
}

async function showClaimDetail(claimId) {
  const modal = document.getElementById('claim-modal');
  const body = document.getElementById('claim-modal-body');
  modal.classList.remove('hidden');
  body.innerHTML = '<div class="flex justify-center py-8"><span class="spinner"></span></div>';
  try {
    const data = await apiFetch(`${API_V19}/billing/claim-status/${claimId}`);
    const s = data.status || {};
    body.innerHTML = `<div class="space-y-4">
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div><span class="text-gray-500">Claim ID:</span> <span class="font-mono">${s.claim_id || claimId}</span></div>
        <div><span class="text-gray-500">Status:</span> ${statusBadge(s.status)}</div>
        <div><span class="text-gray-500">Payer:</span> ${s.payer_name || '—'}</div>
        <div><span class="text-gray-500">Charges:</span> ${fmtMoney(s.total_charges)}</div>
      </div>
      <h4 class="font-semibold text-gray-700 mt-4">History</h4>
      <div class="text-sm space-y-2">${(data.history || []).map(h => `<div class="flex gap-3"><span class="text-gray-400">${formatDate(h.timestamp)}</span><span>${h.event || h.action}</span></div>`).join('') || '<p class="text-gray-400">No history</p>'}</div>
    </div>`;
  } catch { body.innerHTML = '<p class="text-red-500">Failed to load claim details</p>'; }
}

function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

// ── Coding Tab ──────────────────────────────────────────────────────────

async function loadCoding() {
  showLoading(document.getElementById('coding-table-body'));
  try {
    const data = await apiFetch(`/api/history?limit=100`);
    const sessions = data.sessions || [];
    renderCodingTable(sessions);
  } catch {
    document.getElementById('coding-table-body').innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-400">No data</td></tr>';
  }
}

function renderCodingTable(sessions) {
  const tbody = document.getElementById('coding-table-body');
  if (!sessions.length) { tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-400">No coding sessions</td></tr>'; return; }
  tbody.innerHTML = sessions.map(s => {
    const cpt = (s.cpt_codes || s.codes || []).map(c => c.code || c).join(', ') || '—';
    const icd = (s.icd_codes || []).map(c => c.code || c).join(', ') || '—';
    const conf = s.confidence || s.confidence_overall;
    const confPct = conf != null ? Math.round(conf * 100) + '%' : '—';
    return `<tr onclick="showCodingDetail('${escapeHtml(s.session_id)}')">
      <td class="font-mono text-xs">${escapeHtml(s.session_id) || '—'}</td>
      <td>${escapeHtml(s.note_type || s.encounter_type) || '—'}</td>
      <td class="font-mono text-xs">${cpt}</td>
      <td class="font-mono text-xs">${icd}</td>
      <td>${confPct}</td>
      <td>${formatDate(s.created_at || s.timestamp)}</td>
    </tr>`;
  }).join('');
}

async function showCodingDetail(sessionId) {
  const modal = document.getElementById('coding-modal');
  const body = document.getElementById('coding-modal-body');
  modal.classList.remove('hidden');
  body.innerHTML = '<div class="flex justify-center py-8"><span class="spinner"></span></div>';
  try {
    const data = await apiFetch(`/api/session/${sessionId}`);
    const codes = data.codes || data.cpt_codes || [];
    body.innerHTML = `<div class="space-y-4">
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div><span class="text-gray-500">Session:</span> <span class="font-mono">${escapeHtml(sessionId)}</span></div>
        <div><span class="text-gray-500">Note Type:</span> ${escapeHtml(data.note_type) || '—'}</div>
        <div><span class="text-gray-500">Confidence:</span> ${data.confidence != null ? Math.round(data.confidence * 100) + '%' : '—'}</div>
        <div><span class="text-gray-500">Date:</span> ${formatDate(data.created_at)}</div>
      </div>
      <h4 class="font-semibold text-gray-700 mt-4">Codes</h4>
      <div class="space-y-2">${codes.map(c => `<div class="flex items-center gap-2 text-sm"><span class="font-mono bg-gray-100 px-2 py-0.5 rounded">${c.code || c}</span><span>${c.description || ''}</span></div>`).join('') || '<p class="text-gray-400">No codes</p>'}</div>
    </div>`;
  } catch { body.innerHTML = '<p class="text-red-500">Failed to load session details</p>'; }
}

// ── Users Tab ───────────────────────────────────────────────────────────

async function loadUsers() {
  showLoading(document.getElementById('users-table-body'));
  try {
    const data = await apiFetch(`${API_V19}/auth/stats`);
    const users = data.users?.users || data.users || [];
    renderUsersTable(Array.isArray(users) ? users : []);
  } catch {
    document.getElementById('users-table-body').innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-400">No data</td></tr>';
  }
}

function renderUsersTable(users) {
  const tbody = document.getElementById('users-table-body');
  if (!users.length) { tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-400">No users</td></tr>'; return; }
  tbody.innerHTML = users.map(u => `<tr>
    <td>${u.username || u.user_id || '—'}</td>
    <td><span class="badge badge-submitted">${u.role || '—'}</span></td>
    <td>${formatDate(u.last_login)}</td>
    <td>${u.is_active !== false ? '<span class="text-green-600">Active</span>' : '<span class="text-red-500">Inactive</span>'}</td>
    <td><button class="text-indigo-600 hover:text-indigo-800 text-xs font-medium">Edit</button></td>
  </tr>`).join('');
}

function showAddUserModal() {
  document.getElementById('add-user-modal').classList.remove('hidden');
}

async function submitNewUser() {
  const username = document.getElementById('new-username').value.trim();
  const password = document.getElementById('new-password').value;
  const role = document.getElementById('new-role').value;
  if (!username || !password) { showToast('Username and password are required', 'error'); return; }
  const btn = document.getElementById('create-user-btn');
  btn.disabled = true; btn.textContent = 'Creating...';
  try {
    await apiFetch(`${API_V19}/auth/register`, {
      method: 'POST',
      body: JSON.stringify({ username, password, role }),
    });
    showToast(`User "${username}" created`, 'success');
    closeModal('add-user-modal');
    document.getElementById('new-username').value = '';
    document.getElementById('new-password').value = '';
    loadUsers();
  } catch (e) { console.error('User creation failed:', e); }
  finally { btn.disabled = false; btn.textContent = 'Create User'; }
}

// ── Reports Tab ─────────────────────────────────────────────────────────

function loadReports() {
  loadReportHistory();
}

async function loadReportHistory() {
  try {
    const data = await apiFetch(`${API_BASE}/activity?limit=50`);
    const reports = (data.events || []).filter(e => {
      const t = (e.type || '').toLowerCase();
      const d = (e.description || '').toLowerCase();
      return t.includes('report') || d.includes('report') || d.includes('generated');
    });
    const tbody = document.getElementById('report-history-body');
    if (!reports.length) { tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-gray-400">No reports generated yet</td></tr>'; return; }
    tbody.innerHTML = reports.map(r => `<tr>
      <td>${escapeHtml(r.type) || '—'}</td>
      <td>${formatDate(r.timestamp)}</td>
      <td>${statusBadge(r.status || 'completed')}</td>
      <td><a href="${API_V19}/reports/${escapeHtml(r.type)}" class="text-indigo-600 hover:text-indigo-800 text-xs font-medium" target="_blank">Download</a></td>
    </tr>`).join('');
  } catch {
    document.getElementById('report-history-body').innerHTML = '<tr><td colspan="4" class="text-center py-4 text-gray-400">No data</td></tr>';
  }
}

async function generateReport(type) {
  showToast(`Generating ${type} report...`, 'info');
  try {
    const res = await fetch(`${API_V19}/reports/${type}`, { headers: authHeaders() });
    if (!res.ok) throw new Error('Generation failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type}_report.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`${type} report downloaded`, 'success');
  } catch (e) { showToast(`Failed: ${e.message}`, 'error'); }
}

// ── Settings Tab ────────────────────────────────────────────────────────

async function loadSettings() {
  try {
    const data = await apiFetch(`${API_BASE}/stats`);
    document.getElementById('sys-version').textContent = data.version || '19.0.0-hipaa';
    document.getElementById('sys-db').textContent = data.db_status || 'Connected';
    document.getElementById('sys-uptime').textContent = data.uptime || '—';
  } catch (e) { console.error('Failed to load settings:', e); }
}

// ── Init ────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  tabs.forEach(t => {
    document.getElementById('tab-btn-' + t)?.addEventListener('click', () => switchTab(t));
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop:not(.hidden)').forEach(m => m.classList.add('hidden'));
    }
  });
  document.querySelectorAll('.toggle').forEach(toggle => {
    toggle.addEventListener('click', () => {
      const dot = toggle.querySelector('.toggle-dot');
      if (toggle.classList.contains('bg-green-500')) {
        toggle.classList.replace('bg-green-500', 'bg-gray-300');
        dot.classList.replace('translate-x-5', 'translate-x-0');
      } else {
        toggle.classList.replace('bg-gray-300', 'bg-green-500');
        dot.classList.replace('translate-x-0', 'translate-x-5');
      }
    });
  });
  switchTab('overview');
});
