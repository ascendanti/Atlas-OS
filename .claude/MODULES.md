# Atlas Personal OS - Module Catalog

**Purpose:** Quick reference for all modules and their purposes

---

## Core Modules (`modules/core/`)

### database.py
**Purpose:** SQLite connection manager, migrations, query helpers
**Status:** Not started
**Key Functions:**
- `connect()` - Get database connection
- `execute()` - Execute SQL with params
- `migrate()` - Run schema migrations

### config.py
**Purpose:** Configuration file manager (YAML/JSON)
**Status:** Not started
**Key Functions:**
- `load_config()` - Load user settings
- `save_config()` - Save settings
- `get()` - Get config value

### utils.py
**Purpose:** Common utilities (date formatting, validation, etc.)
**Status:** Not started

---

## Financial Modules (`modules/financial/`)

### stock_analyzer.py
**Purpose:** Fetch stock data, analyze trends (NO AI needed)
**Status:** Not started
**Data Sources:** Yahoo Finance API, Alpha Vantage (free tier)

### budget_tracker.py
**Purpose:** Track income/expenses, connect to Google Sheets
**Status:** Not started
**Integration:** Google Sheets API

### portfolio_manager.py
**Purpose:** Track investments, calculate returns
**Status:** Not started

---

## Career Modules (`modules/career/`)

### publication_tracker.py
**Purpose:** Track publications, submissions, citations
**Status:** Not started

### cv_manager.py
**Purpose:** Manage CV versions, generate formats
**Status:** Not started

---

## Content Modules (`modules/content/`)

### youtube_planner.py
**Purpose:** Plan videos, track progress, analytics
**Status:** Not started

### podcast_scheduler.py
**Purpose:** Schedule episodes, manage guests
**Status:** Not started

---

## Life Management Modules (`modules/life/`)

### contact_manager.py
**Purpose:** Modern "rolodex" with reminder system
**Status:** Not started
**Features:**
- Track last contact date
- Birthday reminders
- Address book for letter writing

### habit_tracker.py
**Purpose:** Daily habit tracking, streaks
**Status:** Not started

### goal_manager.py
**Purpose:** Goal setting, progress tracking
**Status:** Not started

---

## Knowledge Modules (`modules/knowledge/`)

### pdf_library.py
**Purpose:** Index PDFs, search content, extract metadata
**Status:** Not started
**Libraries:** PyPDF2, pdfplumber

### note_manager.py
**Purpose:** Markdown note system with tagging
**Status:** Not started

---

## Module Development Order (Recommended)

**Phase 1 - Foundation:**
1. core/database.py
2. core/config.py
3. core/utils.py

**Phase 2 - Quick Wins:**
4. life/contact_manager.py (immediate value)
5. life/habit_tracker.py (simple, useful)

**Phase 3 - High Impact:**
6. financial/stock_analyzer.py
7. financial/budget_tracker.py
8. content/youtube_planner.py

**Phase 4 - Long Term:**
9. knowledge/pdf_library.py
10. career/publication_tracker.py
