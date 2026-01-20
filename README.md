# Atlas Personal OS

**Local-first Python automation system for life optimization**

## Vision

A comprehensive personal operating system that runs entirely on your local machine with zero runtime AI costs. Built with Python, SQLite, and modular architecture.

## Features (Planned)

### 🏗️ Core Infrastructure
- [x] Project structure
- [ ] SQLite database manager
- [ ] Task tracking system
- [ ] Configuration management

### 💰 Financial Management
- [ ] Stock market analysis
- [ ] Portfolio tracking
- [ ] Budget analyzer (Google Sheets integration)
- [ ] Investment calculator

### 📚 Career Development
- [ ] Publication tracker
- [ ] CV/Resume manager
- [ ] Job application tracker
- [ ] Research paper monitor

### 🎬 Content Creation
- [ ] YouTube video planner
- [ ] Podcast episode scheduler
- [ ] Social media calendar
- [ ] Content idea bank

### 🏡 Life Management
- [ ] Contact manager ("Modern Rolodex")
- [ ] Habit tracker
- [ ] Goal manager
- [ ] Event reminder system

### 📖 Knowledge Management
- [ ] PDF library indexer
- [ ] Note manager
- [ ] Research tracker
- [ ] Citation manager

## Installation

```bash
# Clone or navigate to project
cd atlas-personal-os

# Install dependencies
pip install -r requirements.txt

# Run CLI
python main.py --help
```

## Usage

```bash
# Task management
python main.py task list
python main.py task add "Buy groceries"

# Financial tools
python main.py finance portfolio

# Life management
python main.py life contacts
```

## Architecture

```
atlas-personal-os/
├── .claude/           # Project tracking & memory
├── modules/           # Feature modules
│   ├── core/         # Core utilities
│   ├── financial/    # Financial tools
│   ├── career/       # Career management
│   ├── content/      # Content creation
│   ├── life/         # Life management
│   └── knowledge/    # Knowledge management
├── tests/            # Automated tests
├── data/             # SQLite databases
├── config/           # Configuration files
├── main.py           # CLI entry point
└── requirements.txt  # Python dependencies
```

## Development

```bash
# Run tests
pytest tests/

# Format code
black .

# Lint code
ruff check .
```

## Technology Stack

- **Language:** Python 3.12.3
- **Database:** SQLite (local, no server)
- **Testing:** pytest
- **CLI:** Click
- **APIs:** As needed (Google Sheets, Yahoo Finance, etc.)

## Philosophy

- **Local-first:** All data stays on your machine
- **Zero AI runtime:** Claude builds it, Python runs it forever
- **Modular:** Each feature is independent
- **Testable:** Every module has automated tests
- **Free to run:** No ongoing costs after development

## License

Personal use

## Author

Built for personal optimization and life management
