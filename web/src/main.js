/**
 * Atlas Personal OS - Web UI
 *
 * Frontend JavaScript for the web interface.
 * Communicates with FastAPI backend at /api endpoints.
 */

const API_BASE = '/api';

// Tab navigation
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const contents = document.querySelectorAll('.tab-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.dataset.tab + '-tab';

      tabs.forEach(t => t.classList.remove('active'));
      contents.forEach(c => c.classList.add('hidden'));

      tab.classList.add('active');
      document.getElementById(targetId).classList.remove('hidden');

      // Load data for the tab
      loadTabData(tab.dataset.tab);
    });
  });
}

// Load data based on active tab
function loadTabData(tab) {
  switch(tab) {
    case 'tasks': loadTasks(); break;
    case 'audit': loadEvents(); break;
    case 'goals': loadGoals(); break;
    case 'notes': loadNotes(); break;
  }
}

// Tasks
async function loadTasks() {
  const container = document.getElementById('tasks-list');
  try {
    const response = await fetch(`${API_BASE}/tasks`);
    const tasks = await response.json();

    if (tasks.length === 0) {
      container.innerHTML = '<div class="empty-state">No tasks yet. Add one above!</div>';
      return;
    }

    container.innerHTML = tasks.map(task => `
      <div class="task-item ${task.status === 'completed' ? 'completed' : ''}" data-id="${task.id}">
        <div class="flex items-center gap-4">
          <input type="checkbox" ${task.status === 'completed' ? 'checked' : ''}
                 onchange="toggleTask(${task.id})" class="w-5 h-5">
          <div>
            <div class="font-medium ${task.status === 'completed' ? 'line-through' : ''}">${task.title}</div>
            <div class="text-sm text-gray-500">${task.category || 'No category'}</div>
          </div>
        </div>
        <span class="task-priority ${task.priority.toLowerCase()}">${task.priority}</span>
      </div>
    `).join('');
  } catch (error) {
    container.innerHTML = '<div class="empty-state text-red-500">Failed to load tasks. Is the API running?</div>';
    console.error('Failed to load tasks:', error);
  }
}

async function addTask(event) {
  event.preventDefault();

  const title = document.getElementById('task-title').value.trim();
  const priority = document.getElementById('task-priority').value;
  const category = document.getElementById('task-category').value.trim();

  if (!title) return;

  try {
    await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, priority, category })
    });

    document.getElementById('task-title').value = '';
    document.getElementById('task-category').value = '';
    loadTasks();
  } catch (error) {
    console.error('Failed to add task:', error);
  }
}

async function toggleTask(taskId) {
  try {
    await fetch(`${API_BASE}/tasks/${taskId}/complete`, { method: 'POST' });
    loadTasks();
  } catch (error) {
    console.error('Failed to toggle task:', error);
  }
}

// Events (Audit)
async function loadEvents() {
  const container = document.getElementById('events-list');
  try {
    const response = await fetch(`${API_BASE}/events`);
    const events = await response.json();

    if (events.length === 0) {
      container.innerHTML = '<div class="empty-state">No events recorded yet.</div>';
      return;
    }

    container.innerHTML = events.map(event => `
      <div class="event-item" onclick="showEventPayload(${JSON.stringify(event).replace(/"/g, '&quot;')})">
        <div class="flex justify-between items-center">
          <span class="font-medium text-atlas-primary">${event.event_type}</span>
          <span class="text-sm text-gray-500">${event.timestamp}</span>
        </div>
        <div class="text-sm text-gray-600 mt-1">
          ${event.entity_type} #${event.entity_id}
        </div>
      </div>
    `).join('');
  } catch (error) {
    container.innerHTML = '<div class="empty-state text-red-500">Failed to load events.</div>';
    console.error('Failed to load events:', error);
  }
}

function showEventPayload(event) {
  const payloadEl = document.getElementById('event-payload');
  payloadEl.textContent = JSON.stringify(event.payload, null, 2);

  document.querySelectorAll('.event-item').forEach(el => el.classList.remove('selected'));
  event.target?.closest('.event-item')?.classList.add('selected');
}

// Goals
async function loadGoals() {
  const container = document.getElementById('goals-list');
  try {
    const response = await fetch(`${API_BASE}/goals`);
    const goals = await response.json();

    if (goals.length === 0) {
      container.innerHTML = '<div class="empty-state">No goals defined yet.</div>';
      return;
    }

    container.innerHTML = goals.map(goal => `
      <div class="p-4 border rounded-lg mb-3">
        <div class="font-medium">${goal.title}</div>
        <div class="text-sm text-gray-500 mt-1">Target: ${goal.target_date || 'Not set'}</div>
        <div class="mt-2 bg-gray-200 rounded-full h-2">
          <div class="bg-atlas-secondary h-2 rounded-full" style="width: ${goal.progress || 0}%"></div>
        </div>
      </div>
    `).join('');
  } catch (error) {
    container.innerHTML = '<div class="empty-state text-red-500">Failed to load goals.</div>';
    console.error('Failed to load goals:', error);
  }
}

// Notes
async function loadNotes() {
  const container = document.getElementById('notes-list');
  try {
    const response = await fetch(`${API_BASE}/notes`);
    const notes = await response.json();

    if (notes.length === 0) {
      container.innerHTML = '<div class="empty-state">No notes yet.</div>';
      return;
    }

    container.innerHTML = notes.map(note => `
      <div class="p-4 border rounded-lg mb-3">
        <div class="font-medium">${note.title}</div>
        <div class="text-sm text-gray-500 mt-1">${note.tags || 'No tags'}</div>
      </div>
    `).join('');
  } catch (error) {
    container.innerHTML = '<div class="empty-state text-red-500">Failed to load notes.</div>';
    console.error('Failed to load notes:', error);
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initTabs();

  // Form handlers
  document.getElementById('add-task-form').addEventListener('submit', addTask);
  document.getElementById('refresh-events')?.addEventListener('click', loadEvents);

  // Load initial data
  loadTasks();
});

// Expose functions globally for inline handlers
window.toggleTask = toggleTask;
window.showEventPayload = showEventPayload;
