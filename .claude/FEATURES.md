# Features

## Backlog
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
- (KNOW-002 completed)

## Acceptance Criteria

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
- KNOW-002 Note Manager (Event-sourced) ✓ (2026-01-20)

## Proceed vs Blocked
- Proceed: CORE-004, FIN-003, FIN-004, FIN-005, CAR-001, CAR-002, CAR-003, CAR-004, CON-001, CON-002, CON-003, CON-004, LIFE-003, LIFE-004, KNOW-001, KNOW-002, KNOW-003, KNOW-004
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

---

## Feature Completion Tracking

**Total Features:** 28
**Complete:** 11
**In Progress:** 0
**Planned:** 18

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
- KNOW-002: Note Manager (Event-sourced)

**Next Sprint:** Content & Knowledge Management

## Decision Needed
- None
