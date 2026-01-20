# Atlas Personal OS - Feature Registry

**Query Format:** `/feature [module] [status]`

**Status Codes:**
- `planned` - Design phase
- `active` - Currently building
- `testing` - Implementation done, testing
- `complete` - Tested and working
- `blocked` - Cannot proceed (dependency/issue)
- `deferred` - Not priority right now

---

## Core Features

| ID | Feature | Status | Priority | Dependencies |
|---|---|---|---|---|
| CORE-001 | SQLite Database Manager | complete | HIGH | None |
| CORE-002 | Task Tracker CLI | complete | HIGH | CORE-001 |
| CORE-003 | Configuration Manager | complete | MEDIUM | CORE-001 |
| CORE-004 | Logging System | planned | LOW | None |

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
**Complete:** 8
**In Progress:** 0
**Planned:** 21

**Completed Features:**
- SPRINT-0000: Dual-agent coordination protocol + WORKING_NOTES.md
- CORE-001: SQLite Database Manager
- CORE-002: Task Tracker CLI
- CORE-003: Configuration Manager
- FIN-001: Stock Market Data Fetcher
- FIN-002: Portfolio Tracker
- LIFE-001: Contact Manager (Rolodex)
- LIFE-002: Habit Tracker

**Next Sprint:** Content & Knowledge Management
