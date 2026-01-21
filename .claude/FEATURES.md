# Features

## Backlog
- CORE-004 Logging System
- UI-001 Desktop Demo Shell (Tkinter Lens)
- UI-002 Tasks Lens (List/Add/Complete)
- UI-003 Audit Lens (Event Stream + Explain)
- UI-004 Event Emission Integration (Tasks → Events)
- UI-005 Keyboard Shortcuts + Empty States
- FIN-003 Budget Analyzer (Google Sheets)
- FIN-004 Expense Categorizer
- FIN-005 Investment Calculator
- CAR-001 Publication Tracker
- CAR-002 CV/Resume Manager
- CAR-003 Job Application Tracker
- CAR-004 Research Paper Monitor (RSS)
- CON-001 YouTube Video Planner
- CON-002 Podcast Episode Scheduler
- CON-003 Social Media Calendar
- CON-004 Content Idea Bank
- LIFE-003 Goal Manager
- LIFE-004 Event Reminder System
- KNOW-001 PDF Library Indexer
- KNOW-002 Note Manager
- KNOW-003 Research Tracker
- KNOW-004 Citation Manager

## Next
- FIN-003 Budget Analyzer
- FIN-004 Expense Categorizer
- CAR-004 Research Paper Monitor

## Recently Enhanced (2026-01-20)
### LIFE-005 Enhanced Task Tracker (GTD Edition)
- Subtasks with parent_id hierarchy
- Multiple tags (JSON array)
- Time tracking (estimated/actual minutes, log_time)
- Task dependencies (blocked_by)
- Recurring tasks (daily/weekly/monthly/yearly)
- GTD views: today, upcoming, someday, overdue, blocked
- Context and energy level filtering
- Goal linkage

### LIFE-006 Enhanced Goal Manager (OKR Edition)
- Areas of life (health, career, finance, relationships, etc.)
- Key Results (OKR-style measurable metrics)
- Milestones with completion tracking
- Goal hierarchy (parent/child goals)
- Progress history with reflections

### LIFE-007 Weekly Review System
- Generate weekly/monthly/quarterly reviews
- Aggregate metrics from tasks, goals, habits
- Reflection prompts (GTD-style)
- Review persistence and history
- Trend analysis across reviews

### API-002 Enhanced Web API v2.1
- 50+ new endpoints for GTD and OKR features
- Task GTD views: /api/tasks/today, /api/tasks/upcoming, etc.
- Goal OKR: /api/goals/{id}/key-results, /api/goals/{id}/milestones
- Weekly reviews: /api/reviews/generate, /api/reviews/trends

## Acceptance Criteria

### UI-001 Desktop Demo Shell
- Tkinter app launches with `python main.py ui`
- Two tabs: "Tasks" and "Audit"
- Clean window layout with tab navigation
- Works 100% offline

### UI-002 Tasks Lens
- Lists tasks from TaskTracker.list() in a table
- Add Task form (title, priority, category)
- Complete Task button for selected row
- Uses module command functions (no direct SQL)
- Refreshes list after add/complete (no restart)
- Basic empty states + minimal error messaging

### UI-003 Audit Lens
- Lists recent events from EventStore.query()
- Columns: timestamp, event_type, entity_type, entity_id
- Click event to show payload JSON in detail pane
- Confirms TASK_CREATED and TASK_COMPLETED events appear

### CORE-004 Event Spine + Audit Log
- `events` table: id, event_type, entity_type, entity_id, payload (JSON), timestamp
- `emit_event(event_type, entity_type, entity_id, payload)` → inserts event
- `query_events(entity_type?, entity_id?, event_type?, since?)` → filtered events
- `explain(entity_type, entity_id)` → chronological event history for entity
- ≥1 existing feature emits 1 event (e.g., task creation)
- Unit tests for emit/query/explain
- Works 100% offline, <200 lines

### LIFE-003 Goal Manager (Goals-as-projection)
- Events: GOAL_DEFINED, GOAL_TARGET_SET, GOAL_UPDATED
- Goals projection computed from events only (no direct table mutation)
- CLI: `goal define <title>`, `goal set-target <id> <target_date>`, `goal list`, `goal progress <id>`
- Progress derived from events (percentage toward target)
- Unit tests for goal define + progress projection
- Works 100% offline, <200 lines

### KNOW-002 Note Manager (Event-sourced)
- Events: NOTE_CREATED, NOTE_UPDATED, NOTE_ARCHIVED, NOTE_TAGGED
- Notes projection from events (title, content, tags, timestamps)
- CLI: `note create <title>`, `note edit <id>`, `note list`, `note search <query>`, `note show <id>`, `note tag <id> <tags>`
- Full-text search on title and content
- Tag-based organization
- Unit tests for CRUD + search
- Works 100% offline, <200 lines

### CON-001 YouTube Video Planner (Event-sourced)
- Events: VIDEO_PLANNED, VIDEO_SCRIPTED, VIDEO_RECORDED, VIDEO_EDITED, VIDEO_PUBLISHED
- Video fields: title, description, idea_id (links to idea_bank), script_status, recording_date, publish_date, duration_estimate, thumbnail_status, tags
- Status workflow: planned → scripted → recorded → edited → published
- CLI: `video plan <title>`, `video list`, `video show <id>`, `video script <id>`, `video record <id>`, `video edit <id>`, `video publish <id>`, `video explain <id>`
- Links to existing ideas from idea_bank (optional)
- Unit tests for workflow transitions
- Works 100% offline, <200 lines

### CAR-001 Publication Tracker (Event-sourced)
- Events: PUB_CREATED, PUB_UPDATED, PUB_SUBMITTED, PUB_ACCEPTED, PUB_REJECTED, PUB_PUBLISHED
- Publication fields: title, authors, venue (journal/conference/preprint), status, submission_date, publication_date, doi, url, abstract, tags
- Status workflow: draft → submitted → (accepted|rejected) → published
- CLI: `pub add <title>`, `pub list`, `pub show <id>`, `pub submit <id>`, `pub accept <id>`, `pub reject <id>`, `pub publish <id>`, `pub explain <id>`
- Filter by venue type and status
- Unit tests for workflow transitions
- Works 100% offline, <200 lines

### KNOW-001 PDF Library Indexer (Event-sourced)
- Events: PDF_INDEXED, PDF_UPDATED, PDF_TAGGED, PDF_ARCHIVED
- PDF fields: title, authors, file_path, page_count, indexed_at, tags, notes, category
- CLI: `pdf index <path>`, `pdf list`, `pdf show <id>`, `pdf search <query>`, `pdf tag <id> <tags>`, `pdf note <id> <note>`, `pdf explain <id>`
- Full-text search on title, authors, notes
- Tag-based organization
- Unit tests for CRUD + search
- Works 100% offline, <200 lines

### CON-002 Podcast Episode Scheduler (Event-sourced)
- Events: EPISODE_PLANNED, EPISODE_UPDATED, EPISODE_OUTLINED, EPISODE_RECORDED, EPISODE_EDITED, EPISODE_PUBLISHED
- Episode fields: title, description, guest, episode_number, duration_estimate, tags, status, recording_date, publish_date, audio_url
- Status workflow: planned → outlined → recorded → edited → published
- CLI: `podcast plan <title>`, `podcast list`, `podcast show <id>`, `podcast outline <id>`, `podcast record <id>`, `podcast edit <id>`, `podcast publish <id>`, `podcast explain <id>`
- Links to existing ideas from idea_bank (optional)
- Unit tests for workflow transitions
- Works 100% offline, <200 lines

### CON-004 Content Idea Bank (Event-sourced)
- Events: IDEA_CREATED, IDEA_UPDATED, IDEA_STATUS_CHANGED, IDEA_PRIORITIZED
- Idea fields: title, description, platform (youtube/podcast/blog/social), status (draft/planned/in_progress/published/archived), priority
- CLI: `idea add <title>`, `idea list`, `idea show <id>`, `idea update <id>`, `idea status <id> <status>`, `idea prioritize <id> <priority>`
- Filter by platform and status
- Unit tests for CRUD + filtering
- Works 100% offline, <200 lines

### LIFE-004 Event Reminder System (Event-sourced)
- Events: REMINDER_CREATED, REMINDER_UPDATED, REMINDER_TRIGGERED, REMINDER_SNOOZED, REMINDER_COMPLETED, REMINDER_ARCHIVED
- Reminder fields: title, description, event_date, event_time, reminder_minutes, recurrence (none/daily/weekly/monthly), contact_id (optional link to contact), tags
- CLI: `reminder add <title>`, `reminder list`, `reminder show <id>`, `reminder upcoming`, `reminder complete <id>`, `reminder snooze <id>`, `reminder archive <id>`, `reminder explain <id>`
- Filter by date range and tags
- Links to contacts (optional) from LIFE-001
- Unit tests for CRUD + date filtering
- Works 100% offline, <200 lines

## In Progress
- None

## Done
- CORE-001 SQLite Database Manager
- CORE-002 Task Tracker CLI
- CORE-003 Configuration Manager
- CORE-004 Event Spine + Audit Log ✓ (2026-01-20)
- FIN-001 Stock Market Data Fetcher
- FIN-002 Portfolio Tracker
- LIFE-001 Contact Manager (Rolodex)
- LIFE-002 Habit Tracker
- LIFE-003 Goal Manager (Goals-as-projection) ✓ (2026-01-20)
- LIFE-004 Event Reminder System ✓ (2026-01-20)
- KNOW-002 Note Manager (Event-sourced) ✓ (2026-01-20)
- CON-004 Content Idea Bank (Event-sourced) ✓ (2026-01-20)
- UI-001 Desktop Demo Shell ✓ (2026-01-20)
- UI-002 Tasks Lens ✓ (2026-01-20)
- UI-003 Audit Lens ✓ (2026-01-20)
- CON-001 YouTube Video Planner ✓ (2026-01-20)
- CAR-001 Publication Tracker ✓ (2026-01-20)
- KNOW-001 PDF Library Indexer ✓ (2026-01-20)
- CON-002 Podcast Episode Scheduler ✓ (2026-01-20)
- CAR-002 CV/Resume Manager ✓ (2026-01-20)
- LIFE-005 Enhanced Task Tracker (GTD Edition) ✓ (2026-01-20)
- LIFE-006 Enhanced Goal Manager (OKR Edition) ✓ (2026-01-20)
- LIFE-007 Weekly Review System ✓ (2026-01-20)
- API-002 Enhanced Web API v2.1 ✓ (2026-01-20)
- KNOW-003 Research Tracker ✓ (2026-01-20)
- CAR-003 Job Application Tracker ✓ (2026-01-20)
- CON-003 Social Media Calendar ✓ (2026-01-20)

## Proceed vs Blocked
- Proceed: UI-001, UI-002, UI-003, UI-004, UI-005, CORE-004, FIN-003, FIN-004, FIN-005, CAR-001, CAR-002, CAR-003, CAR-004, CON-001, CON-002, CON-003, CON-004, LIFE-003, LIFE-004, KNOW-001, KNOW-002, KNOW-003, KNOW-004
- Blocked: None

## Financial Features

| ID | Feature | Status | Priority | Dependencies |
|---|---|---|---|---|
| FIN-001 | Stock Market Data Fetcher | complete | HIGH | CORE-001 |
| FIN-002 | Portfolio Tracker | complete | HIGH | FIN-001 |
| FIN-003 | Budget Analyzer (Google Sheets) | planned | MEDIUM | CORE-001 |
| FIN-004 | Expense Categorizer | planned | MEDIUM | FIN-003 |
| FIN-005 | Investment Calculator | planned | LOW | FIN-002 |

## Career Features

| ID | Feature | Status | Priority | Dependencies |
|---|---|---|---|---|
| CAR-001 | Publication Tracker | planned | MEDIUM | CORE-001 |
| CAR-002 | CV/Resume Manager | planned | MEDIUM | CORE-001 |
| CAR-003 | Job Application Tracker | planned | LOW | CORE-001 |
| CAR-004 | Research Paper Monitor (RSS) | planned | LOW | CORE-001 |

## Content Features

| ID | Feature | Status | Priority | Dependencies |
|---|---|---|---|---|
| CON-001 | YouTube Video Planner | planned | MEDIUM | CORE-001 |
| CON-002 | Podcast Episode Scheduler | planned | MEDIUM | CORE-001 |
| CON-003 | Social Media Calendar | planned | LOW | CON-001 |
| CON-004 | Content Idea Bank | planned | LOW | CORE-001 |

## Life Management Features

| ID | Feature | Status | Priority | Dependencies |
|---|---|---|---|---|
| LIFE-001 | Contact Manager ("Rolodex") | complete | HIGH | CORE-001 |
| LIFE-002 | Habit Tracker | complete | MEDIUM | CORE-001 |
| LIFE-003 | Goal Manager | planned | MEDIUM | CORE-001 |
| LIFE-004 | Event Reminder System | planned | LOW | LIFE-001 |

## Knowledge Features

| ID | Feature | Status | Priority | Dependencies |
|---|---|---|---|---|
| KNOW-001 | PDF Library Indexer | planned | MEDIUM | CORE-001 |
| KNOW-002 | Note Manager | planned | MEDIUM | CORE-001 |
| KNOW-003 | Research Tracker | planned | LOW | KNOW-001 |
| KNOW-004 | Citation Manager | planned | LOW | KNOW-001 |

## UI Features

| ID | Feature | Status | Priority | Dependencies |
|---|---|---|---|---|
| UI-001 | Desktop Demo Shell (Tkinter Lens) | planned | HIGH | CORE-001 |
| UI-002 | Tasks Lens (List/Add/Complete) | planned | HIGH | UI-001 |
| UI-003 | Audit Lens (Event Stream + Explain) | planned | HIGH | UI-001, UI-004 |
| UI-004 | Event Emission Integration (Tasks → Events) | planned | HIGH | CORE-004 |
| UI-005 | Keyboard Shortcuts + Empty States | planned | MEDIUM | UI-001 |

### UI Epic Definitions (DoD + Acceptance)
- **UI-001 Desktop Demo Shell**: Notebook tabs (Today/Tasks/Habits/Goals/Audit), window boot, no data access yet.
  - DoD: App launches, tabs visible, exits cleanly.
  - Acceptance: runs with `python ui/desktop_app.py` (or `atlas_ui.py`).
- **UI-002 Tasks Lens**: Task list + add + complete wired to TaskTracker API.
  - DoD: UI calls TaskTracker only (no SQL), updates list after actions.
  - Acceptance: add/complete reflected in list without restart.
- **UI-003 Audit Lens**: Event list + filters + per-entity explain.
  - DoD: UI uses EventStore query/explain only.
  - Acceptance: Task create/complete events visible with payloads.
- **UI-004 Event Emission Integration**: TASK_CREATED/TASK_COMPLETED emitted by TaskTracker.
  - DoD: EventStore receives events on add/complete.
  - Acceptance: Audit lens shows new events after UI actions.
- **UI-005 Keyboard + Empty States**: shortcuts for add/complete, empty-state guidance.
  - DoD: at least 2 shortcuts documented; empty states shown.
  - Acceptance: no crashes when lists are empty.

---

## Feature Completion Tracking

**Total Features:** 37
**Complete:** 29
**In Progress:** 0
**Planned:** 8

**Completed Features:**
- SPRINT-0000: Dual-agent coordination protocol + WORKING_NOTES.md
- CORE-001: SQLite Database Manager
- CORE-002: Task Tracker CLI
- CORE-003: Configuration Manager
- CORE-004: Event Spine + Audit Log
- FIN-001: Stock Market Data Fetcher
- FIN-002: Portfolio Tracker
- LIFE-001: Contact Manager (Rolodex)
- LIFE-002: Habit Tracker
- LIFE-003: Goal Manager (Goals-as-projection)
- LIFE-004: Event Reminder System (Event-sourced)
- KNOW-002: Note Manager (Event-sourced)
- CON-004: Content Idea Bank (Event-sourced)
- UI-001: Desktop Demo Shell
- UI-002: Tasks Lens
- UI-003: Audit Lens
- CON-001: YouTube Video Planner (Event-sourced)
- CAR-001: Publication Tracker (Event-sourced)
- KNOW-001: PDF Library Indexer (Event-sourced)
- CON-002: Podcast Episode Scheduler (Event-sourced)
- CAR-002: CV/Resume Manager (Event-sourced)

**Next Sprint:** KNOW-003 Research Tracker, CAR-003 Job Application Tracker, CON-003 Social Media Calendar

## Decision Needed
- None (event_store confirmed missing; implement CORE-004 before UI-003).
- None (defaulting to Tkinter for demo lens)
