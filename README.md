# Atlas Personal OS

**Local-first Python automation system for life optimization**

A comprehensive personal operating system that runs entirely on your local machine with zero runtime AI costs. Built with Python, SQLite, and event-sourced architecture.

## Features

### Core Infrastructure
- [x] SQLite Database Manager - Local-first data storage
- [x] Event Store - Event-sourced architecture with full audit trail
- [x] Task Tracker - GTD-style task management with subtasks, tags, dependencies
- [x] Configuration Manager - YAML-based settings

### Life Management
- [x] **Task Tracker** - GTD views (Today/Upcoming/Someday), subtasks, time tracking, recurring tasks
- [x] **Goal Manager** - OKR-style with Key Results, milestones, areas of life
- [x] **Habit Tracker** - Daily habits with streaks and completion rates
- [x] **Contact Manager** - Modern Rolodex with categories and notes
- [x] **Event Reminder** - Recurring reminders with snooze
- [x] **Weekly Review** - GTD-style weekly/monthly/quarterly reviews

### Content Creation
- [x] **Idea Bank** - Content ideas across platforms (YouTube, podcast, blog, social)
- [x] **Video Planner** - YouTube video workflow (plan → script → record → edit → publish)
- [x] **Podcast Scheduler** - Episode planning with guests and outlines
- [x] **Social Calendar** - Multi-platform post scheduling with engagement tracking

### Career Development
- [x] **Publication Tracker** - Academic papers (draft → submitted → published)
- [x] **CV Manager** - Event-sourced resume with export options
- [x] **Job Application Tracker** - Applications, interviews, offers

### Knowledge Management
- [x] **Note Manager** - Full-text search, tags, archiving
- [x] **PDF Library Indexer** - Index and search PDF documents
- [x] **Research Tracker** - Research projects with questions and findings

### Financial (Basic)
- [x] **Portfolio Tracker** - Stock holdings and performance
- [x] **Stock Analyzer** - Market data fetching

### User Interfaces
- [x] **CLI** - Full command-line interface
- [x] **Web UI** - FastAPI backend + Tailwind CSS frontend
- [x] **Desktop UI** - Tkinter-based (basic)

## Quick Start

```bash
# Clone repository
git clone https://github.com/ascendanti/Atlas-OS.git
cd Atlas-OS

# Install dependencies
pip install -r requirements.txt

# Run CLI
python main.py --help

# Start Web UI
python main.py web
# Then open http://localhost:8000

# Or run API and frontend separately:
cd web && npm install && npm run dev  # Frontend on :3000
python -c "from modules.api.server import run_server; run_server()"  # API on :8000
```

## CLI Examples

```bash
# Task management (GTD-style)
python main.py task add "Review quarterly goals" --priority HIGH --tag planning
python main.py task list --status pending
python main.py task today
python main.py task complete 1

# Goals with OKR
python main.py life goals define "Launch MVP"
python main.py life goals set-target 1 2026-03-01
python main.py life goals update 1 50

# Habits
python main.py life habit add "Morning meditation" --frequency daily
python main.py life habit complete 1

# Content planning
python main.py idea add "AI automation tutorial" --platform youtube
python main.py video plan "Getting Started with Atlas OS"

# Research
python main.py research create "Market analysis" --hypothesis "Users want local-first apps"

# Weekly review
python main.py review generate --type weekly
```

## Architecture

```
Atlas-OS/
├── modules/
│   ├── api/           # FastAPI REST server
│   ├── core/          # Database, events, config, utils
│   ├── life/          # Tasks, goals, habits, contacts, reminders, reviews
│   ├── content/       # Ideas, videos, podcasts, social
│   ├── career/        # Publications, CV, job applications
│   ├── knowledge/     # Notes, PDFs, research
│   ├── financial/     # Portfolio, stocks
│   └── ui/            # Desktop Tkinter app
├── web/               # Vite + Tailwind frontend
├── tests/             # pytest test suite (290+ tests)
├── data/              # SQLite databases (auto-created)
├── .claude/           # Project planning & coordination
└── main.py            # CLI entry point
```

## Event-Sourced Architecture

Atlas uses event sourcing for data integrity and auditability:

```
COMMAND → EVENT → PROJECTION
```

- **Events are truth**: All state changes are recorded as immutable events
- **Full audit trail**: Every action is traceable with `explain` commands
- **Projections**: Current state is computed from event history
- **No data loss**: Events are never deleted, only new events added

Example:
```bash
python main.py life goals explain 1
# Shows: GOAL_DEFINED → GOAL_TARGET_SET → GOAL_UPDATED → ...
```

## API Endpoints

The REST API (v2.1) provides 50+ endpoints:

| Category | Endpoints |
|----------|-----------|
| Tasks | `/api/tasks`, `/api/tasks/today`, `/api/tasks/upcoming`, `/api/tasks/overdue` |
| Goals | `/api/goals`, `/api/goals/{id}/key-results`, `/api/goals/{id}/milestones` |
| Reviews | `/api/reviews/generate`, `/api/reviews/trends` |
| Habits | `/api/habits`, `/api/habits/{id}/complete` |
| And more... | See `/docs` for full Swagger documentation |

## Technology Stack

- **Language**: Python 3.12
- **Database**: SQLite (local, no server needed)
- **API**: FastAPI + Pydantic
- **Frontend**: Vite + Tailwind CSS
- **Testing**: pytest (290+ tests, 46% coverage)
- **Architecture**: Event Sourcing

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=modules --cov-report=html

# Format code
black .

# Lint
ruff check .
```

## Philosophy

- **Local-first**: All data stays on your machine
- **Zero AI runtime**: Claude builds it, Python runs it forever
- **Event-sourced**: Full audit trail and data integrity
- **Modular**: Each feature is independent (<200 lines per module)
- **Testable**: Comprehensive test coverage
- **Free to run**: No ongoing costs

## Status

**29 of 37 features complete (78%)**

See [.claude/FEATURES.md](.claude/FEATURES.md) for detailed feature tracking.

## License

Personal use

## Contributing

This is a personal project. Feel free to fork and adapt for your own use.
