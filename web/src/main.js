/**
 * Atlas Personal OS - Web UI
 * Full dashboard for all 22 modules
 */

const API = '/api';

// Navigation
function initNavigation() {
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const section = btn.dataset.section;

      document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(`${section}-section`).classList.add('active');

      loadSection(section);
    });
  });
}

function loadSection(section) {
  const loaders = {
    dashboard: loadDashboard,
    tasks: loadTasks,
    goals: loadGoals,
    habits: loadHabits,
    reminders: loadReminders,
    contacts: loadContacts,
    ideas: loadIdeas,
    videos: loadVideos,
    podcasts: loadPodcasts,
    publications: loadPublications,
    cv: loadCV,
    notes: loadNotes,
    pdfs: loadPDFs,
    portfolio: loadPortfolio,
    events: loadEvents,
  };
  if (loaders[section]) loaders[section]();
}

// Dashboard
async function loadDashboard() {
  const container = document.getElementById('dashboard-grid');
  try {
    const data = await fetch(`${API}/dashboard`).then(r => r.json());
    container.innerHTML = `
      <div class="stat-card" onclick="navigateTo('tasks')">
        <div class="stat-icon">✓</div>
        <div class="stat-value">${data.tasks.pending}</div>
        <div class="stat-label">Pending Tasks</div>
      </div>
      <div class="stat-card" onclick="navigateTo('goals')">
        <div class="stat-icon">🎯</div>
        <div class="stat-value">${data.goals.active}</div>
        <div class="stat-label">Active Goals</div>
      </div>
      <div class="stat-card" onclick="navigateTo('habits')">
        <div class="stat-icon">📅</div>
        <div class="stat-value">${data.habits.completed_today}/${data.habits.total}</div>
        <div class="stat-label">Habits Today</div>
      </div>
      <div class="stat-card" onclick="navigateTo('reminders')">
        <div class="stat-icon">⏰</div>
        <div class="stat-value">${data.reminders.upcoming_week}</div>
        <div class="stat-label">Upcoming Reminders</div>
      </div>
      <div class="stat-card" onclick="navigateTo('notes')">
        <div class="stat-icon">📝</div>
        <div class="stat-value">${data.notes.total}</div>
        <div class="stat-label">Notes</div>
      </div>
      <div class="stat-card" onclick="navigateTo('ideas')">
        <div class="stat-icon">💡</div>
        <div class="stat-value">${data.ideas.total}</div>
        <div class="stat-label">Content Ideas</div>
      </div>
      <div class="stat-card" onclick="navigateTo('videos')">
        <div class="stat-icon">🎬</div>
        <div class="stat-value">${data.videos.total}</div>
        <div class="stat-label">Videos</div>
      </div>
      <div class="stat-card" onclick="navigateTo('podcasts')">
        <div class="stat-icon">🎙️</div>
        <div class="stat-value">${data.podcasts.total}</div>
        <div class="stat-label">Podcasts</div>
      </div>
      <div class="stat-card" onclick="navigateTo('publications')">
        <div class="stat-icon">📄</div>
        <div class="stat-value">${data.publications.total}</div>
        <div class="stat-label">Publications</div>
      </div>
      <div class="stat-card" onclick="navigateTo('cv')">
        <div class="stat-icon">📋</div>
        <div class="stat-value">${data.cv_entries.total}</div>
        <div class="stat-label">CV Entries</div>
      </div>
      <div class="stat-card" onclick="navigateTo('contacts')">
        <div class="stat-icon">👤</div>
        <div class="stat-value">${data.contacts.total}</div>
        <div class="stat-label">Contacts</div>
      </div>
      <div class="stat-card" onclick="navigateTo('events')">
        <div class="stat-icon">📜</div>
        <div class="stat-value">∞</div>
        <div class="stat-label">Audit Events</div>
      </div>
    `;
  } catch (e) {
    container.innerHTML = '<div class="stat-card text-red-400">API not available. Run: python main.py web</div>';
  }
}

function navigateTo(section) {
  document.querySelector(`[data-section="${section}"]`).click();
}

// Tasks
async function loadTasks() {
  const container = document.getElementById('tasks-list');
  try {
    const tasks = await fetch(`${API}/tasks`).then(r => r.json());
    if (!tasks.length) {
      container.innerHTML = '<div class="empty-state">No tasks. Add one above!</div>';
      return;
    }
    container.innerHTML = tasks.map(t => `
      <div class="list-item">
        <div class="flex items-center gap-3">
          <input type="checkbox" class="checkbox" ${t.status === 'completed' ? 'checked' : ''}
                 onchange="completeTask(${t.id})">
          <div>
            <div class="${t.status === 'completed' ? 'line-through text-gray-500' : ''}">${t.title}</div>
            <div class="text-xs text-gray-500">${t.category || 'No category'}</div>
          </div>
        </div>
        <span class="badge badge-${t.priority === 'URGENT' ? 'red' : t.priority === 'HIGH' ? 'yellow' : 'blue'}">${t.priority}</span>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

async function completeTask(id) {
  await fetch(`${API}/tasks/${id}/complete`, { method: 'POST' });
  loadTasks();
}

// Goals
async function loadGoals() {
  const container = document.getElementById('goals-list');
  try {
    const goals = await fetch(`${API}/goals`).then(r => r.json());
    if (!goals.length) { container.innerHTML = '<div class="empty-state">No goals defined</div>'; return; }
    container.innerHTML = goals.map(g => `
      <div class="mb-4">
        <div class="flex justify-between mb-1">
          <span class="font-medium">${g.title}</span>
          <span class="text-sm text-gray-400">${g.percentage.toFixed(0)}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${g.percentage}%"></div>
        </div>
        <div class="text-xs text-gray-500 mt-1">Target: ${g.target_date || 'Not set'}</div>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Habits
async function loadHabits() {
  const container = document.getElementById('habits-list');
  try {
    const habits = await fetch(`${API}/habits`).then(r => r.json());
    if (!habits.length) { container.innerHTML = '<div class="empty-state">No habits tracked</div>'; return; }
    container.innerHTML = habits.map(h => `
      <div class="list-item">
        <div class="flex items-center gap-3">
          <input type="checkbox" class="checkbox" ${h.completed_today ? 'checked' : ''}
                 onchange="completeHabit(${h.id})">
          <div>
            <div>${h.name}</div>
            <div class="text-xs text-gray-500">${h.frequency} • ${h.current_streak} day streak</div>
          </div>
        </div>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

async function completeHabit(id) {
  await fetch(`${API}/habits/${id}/complete`, { method: 'POST' });
  loadHabits();
}

// Reminders
async function loadReminders() {
  const container = document.getElementById('reminders-list');
  try {
    const reminders = await fetch(`${API}/reminders?days=30`).then(r => r.json());
    if (!reminders.length) { container.innerHTML = '<div class="empty-state">No upcoming reminders</div>'; return; }
    container.innerHTML = reminders.map(r => `
      <div class="list-item">
        <div>
          <div>${r.title}</div>
          <div class="text-sm text-gray-400">${r.event_date} ${r.event_time}</div>
        </div>
        <span class="badge badge-${r.recurrence !== 'none' ? 'purple' : 'gray'}">${r.recurrence}</span>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Contacts
async function loadContacts() {
  const container = document.getElementById('contacts-list');
  try {
    const contacts = await fetch(`${API}/contacts`).then(r => r.json());
    if (!contacts.length) { container.innerHTML = '<div class="empty-state">No contacts</div>'; return; }
    container.innerHTML = contacts.map(c => `
      <div class="list-item">
        <div>
          <div class="font-medium">${c.first_name} ${c.last_name}</div>
          <div class="text-sm text-gray-400">${c.email || c.phone || 'No contact info'}</div>
        </div>
        <span class="badge badge-gray">${c.category || 'other'}</span>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Ideas
async function loadIdeas() {
  const container = document.getElementById('ideas-list');
  try {
    const ideas = await fetch(`${API}/ideas`).then(r => r.json());
    if (!ideas.length) { container.innerHTML = '<div class="empty-state">No content ideas</div>'; return; }
    container.innerHTML = ideas.map(i => `
      <div class="list-item">
        <div>
          <div>${i.title}</div>
          <div class="text-sm text-gray-400">${i.platform}</div>
        </div>
        <div class="flex gap-2">
          <span class="badge badge-blue">${i.status}</span>
          <span class="badge badge-gray">P${i.priority}</span>
        </div>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Videos
async function loadVideos() {
  const container = document.getElementById('videos-list');
  try {
    const videos = await fetch(`${API}/videos`).then(r => r.json());
    if (!videos.length) { container.innerHTML = '<div class="empty-state">No videos planned</div>'; return; }
    container.innerHTML = videos.map(v => `
      <div class="list-item">
        <div>
          <div>${v.title}</div>
          <div class="text-sm text-gray-400">${v.duration_estimate ? v.duration_estimate + ' min' : 'No duration set'}</div>
        </div>
        <span class="badge badge-${v.status === 'published' ? 'green' : v.status === 'edited' ? 'blue' : 'yellow'}">${v.status}</span>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Podcasts
async function loadPodcasts() {
  const container = document.getElementById('podcasts-list');
  try {
    const podcasts = await fetch(`${API}/podcasts`).then(r => r.json());
    if (!podcasts.length) { container.innerHTML = '<div class="empty-state">No episodes planned</div>'; return; }
    container.innerHTML = podcasts.map(p => `
      <div class="list-item">
        <div>
          <div>${p.episode_number ? `#${p.episode_number}: ` : ''}${p.title}</div>
          <div class="text-sm text-gray-400">${p.guest ? `Guest: ${p.guest}` : 'No guest'}</div>
        </div>
        <span class="badge badge-${p.status === 'published' ? 'green' : 'yellow'}">${p.status}</span>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Publications
async function loadPublications() {
  const container = document.getElementById('publications-list');
  try {
    const pubs = await fetch(`${API}/publications`).then(r => r.json());
    if (!pubs.length) { container.innerHTML = '<div class="empty-state">No publications</div>'; return; }
    container.innerHTML = pubs.map(p => `
      <div class="list-item">
        <div>
          <div>${p.title}</div>
          <div class="text-sm text-gray-400">${p.authors || 'No authors'} • ${p.venue}</div>
        </div>
        <span class="badge badge-${p.status === 'published' ? 'green' : p.status === 'accepted' ? 'blue' : 'yellow'}">${p.status}</span>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// CV
async function loadCV() {
  const container = document.getElementById('cv-list');
  try {
    const entries = await fetch(`${API}/cv`).then(r => r.json());
    if (!entries.length) { container.innerHTML = '<div class="empty-state">No CV entries</div>'; return; }
    container.innerHTML = entries.map(e => `
      <div class="list-item">
        <div>
          <div>${e.title}</div>
          <div class="text-sm text-gray-400">${e.organization || 'No organization'} ${e.start_date ? `• ${e.start_date} - ${e.end_date || 'present'}` : ''}</div>
        </div>
        <span class="badge badge-purple">${e.entry_type}</span>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Notes
async function loadNotes() {
  const container = document.getElementById('notes-list');
  try {
    const notes = await fetch(`${API}/notes`).then(r => r.json());
    if (!notes.length) { container.innerHTML = '<div class="empty-state">No notes</div>'; return; }
    container.innerHTML = notes.map(n => `
      <div class="list-item">
        <div>
          <div>${n.title}</div>
          <div class="text-sm text-gray-400">${n.tags || 'No tags'}</div>
        </div>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// PDFs
async function loadPDFs() {
  const container = document.getElementById('pdfs-list');
  try {
    const pdfs = await fetch(`${API}/pdfs`).then(r => r.json());
    if (!pdfs.length) { container.innerHTML = '<div class="empty-state">No PDFs indexed</div>'; return; }
    container.innerHTML = pdfs.map(p => `
      <div class="list-item">
        <div>
          <div>${p.title}</div>
          <div class="text-sm text-gray-400">${p.authors || 'Unknown author'} • ${p.page_count || '?'} pages</div>
        </div>
        <span class="badge badge-gray">${p.category}</span>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Portfolio
async function loadPortfolio() {
  const summary = document.getElementById('portfolio-summary');
  const holdings = document.getElementById('portfolio-holdings');
  try {
    const data = await fetch(`${API}/portfolio`).then(r => r.json());
    const sign = data.gain_loss >= 0 ? '+' : '';
    summary.innerHTML = `
      <div class="stat-card">
        <div class="stat-value">${data.holdings_count}</div>
        <div class="stat-label">Holdings</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">$${data.total_cost.toFixed(2)}</div>
        <div class="stat-label">Total Cost</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">$${data.total_value.toFixed(2)}</div>
        <div class="stat-label">Current Value</div>
      </div>
      <div class="stat-card">
        <div class="stat-value ${data.gain_loss >= 0 ? 'text-green-400' : 'text-red-400'}">${sign}$${data.gain_loss.toFixed(2)}</div>
        <div class="stat-label">Gain/Loss (${sign}${data.gain_loss_percent.toFixed(1)}%)</div>
      </div>
    `;
    if (!data.holdings?.length) {
      holdings.innerHTML = '<div class="empty-state">No holdings</div>';
    } else {
      holdings.innerHTML = data.holdings.map(h => `
        <div class="list-item">
          <div>
            <div class="font-medium">${h.symbol}</div>
            <div class="text-sm text-gray-400">${h.shares} shares @ $${h.cost_basis?.toFixed(2) || '?'}</div>
          </div>
        </div>
      `).join('');
    }
  } catch (e) {
    summary.innerHTML = '<div class="stat-card text-red-400">Failed to load</div>';
    holdings.innerHTML = '';
  }
}

// Events (Audit)
async function loadEvents() {
  const container = document.getElementById('events-list');
  try {
    const events = await fetch(`${API}/events?limit=50`).then(r => r.json());
    if (!events.length) { container.innerHTML = '<div class="empty-state">No events recorded</div>'; return; }
    container.innerHTML = events.map(e => `
      <div class="list-item text-sm">
        <div>
          <div class="font-medium text-blue-400">${e.event_type}</div>
          <div class="text-gray-400">${e.entity_type} #${e.entity_id}</div>
        </div>
        <div class="text-xs text-gray-500">${e.timestamp?.slice(0, 19) || ''}</div>
      </div>
    `).join('');
  } catch (e) { container.innerHTML = '<div class="empty-state text-red-400">Failed to load</div>'; }
}

// Task form
document.getElementById('add-task-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = document.getElementById('task-title').value.trim();
  const priority = document.getElementById('task-priority').value;
  if (!title) return;

  await fetch(`${API}/tasks?title=${encodeURIComponent(title)}&priority=${priority}`, { method: 'POST' });
  document.getElementById('task-title').value = '';
  loadTasks();
});

// Init
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  loadDashboard();
});

// Global
window.completeTask = completeTask;
window.completeHabit = completeHabit;
window.navigateTo = navigateTo;
