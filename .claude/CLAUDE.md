# Atlas Personal OS - Master Project Memory

**Last Updated:** 2026-01-19

## Project Overview

**Vision:** Local-first Python automation system integrating financial intelligence, career management, content creation, and life optimization.

**Core Principle:** NO runtime AI dependency. Claude builds it, Python runs it locally forever.

## Project Rules (Read Once Per Session)

1. **Every module MUST:**
   - Be <200 lines OR split into smaller files
   - Have automated tests (pytest)
   - Use SQLite for local storage
   - Work 100% offline (except APIs you explicitly configure)
   - Have zero AI runtime costs

2. **Development Workflow:**
   - Run tests BEFORE commits: `pytest tests/`
   - Update STATUS.md after EVERY change
   - Use modular architecture (modules/ directory)
   - Document in README.md

3. **Token Budget:**
   - Read CLAUDE.md once/session (~1000 tokens)
   - Query FEATURES.md on-demand (~200 tokens/section)
   - Read module docs as needed (~100 tokens/module)

## Directory Structure

```
atlas-personal-os/
├── .claude/                    # Project memory & tracking
│   ├── CLAUDE.md              # This file - master memory
│   ├── FEATURES.md            # Feature registry
│   ├── MODULES.md             # Module catalog
│   └── PROGRESS.md            # Daily log
├── modules/                    # Feature modules
│   ├── core/                  # Core utilities
│   ├── financial/             # Stock analysis, budgeting
│   ├── career/                # Publications, CV, job tracking
│   ├── content/               # YouTube, podcast, social media
│   ├── life/                  # Family, habits, goals
│   └── knowledge/             # PDF library, notes, research
├── tests/                      # Automated tests
├── data/                       # SQLite databases
├── config/                     # Configuration files
├── requirements.txt            # Python dependencies
└── main.py                     # CLI entry point
```

## Technology Stack

- **Language:** Python 3.12.3
- **Database:** SQLite (local, no server needed)
- **Testing:** pytest
- **CLI:** argparse or Click
- **Optional Web UI:** Flask/FastAPI (future)

## Next Steps

1. Create FEATURES.md with feature registry
2. Create MODULES.md with module catalog
3. Build core/database.py for SQLite access
4. Build core/task_tracker.py as first working module
5. Create CLI interface (main.py)
