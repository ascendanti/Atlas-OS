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
- UI-001 Desktop Demo Shell (Tkinter Lens)
- UI-002 Tasks Lens (List/Add/Complete)
- UI-003 Audit Lens (Event Stream + Explain)

## In Progress
- None

## Done
- CORE-001 SQLite Database Manager
- CORE-002 Task Tracker CLI
- CORE-003 Configuration Manager
- FIN-001 Stock Market Data Fetcher
- FIN-002 Portfolio Tracker
- LIFE-001 Contact Manager (Rolodex)
- LIFE-002 Habit Tracker

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

**Total Features:** 33
**Complete:** 8
**In Progress:** 0
**Planned:** 26

**Completed Features:**
- SPRINT-0000: Dual-agent coordination protocol + WORKING_NOTES.md
- CORE-001: SQLite Database Manager
- CORE-002: Task Tracker CLI
- CORE-003: Configuration Manager
- FIN-001: Stock Market Data Fetcher
- FIN-002: Portfolio Tracker
- LIFE-001: Contact Manager (Rolodex)
- LIFE-002: Habit Tracker

**Next Sprint:** Desktop Demo (Tasks + Audit)

## Decision Needed
- Confirm whether `modules/core/event_store.py` exists on the remote branch; UI-003 depends on its API.
