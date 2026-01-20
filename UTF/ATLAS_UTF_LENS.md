# Atlas UTF Lens - Builder's Guide

**For:** Codex (Builder Agent)
**Purpose:** Understanding UTF's role in Atlas-OS architecture
**Status:** Future overlay layer - NOT required for MVP

---

## What is UTF?

**UTF (Universal Task Framework)** is a planned optional overlay layer for Atlas-OS that enhances the core deterministic automation system with intelligent task coordination and natural language interfaces.

**Critical Principle:** UTF is OPTIONAL. All Atlas-OS modules must function completely without UTF.

---

## Architectural Position

```
┌─────────────────────────────────────┐
│   UTF Layer (Optional Overlay)      │
│   - Natural language interfaces     │
│   - Intelligent task suggestions    │
│   - Cross-module coordination       │
└─────────────────────────────────────┘
              ↓ (optional)
┌─────────────────────────────────────┐
│   Atlas Core Modules (Required)     │
│   - Task tracker, Finance, Life     │
│   - SQLite storage, deterministic   │
│   - Works 100% offline, no AI       │
└─────────────────────────────────────┘
```

---

## Design Constraints for UTF Implementation

### 1. Zero Core Dependency
- Core modules MUST NOT import or require UTF
- UTF imports core modules, NEVER the reverse
- UTF failure = graceful degradation to core functionality
- All data storage remains in core SQLite schemas

### 2. Explainability First
UTF must answer: **"Why did Atlas do/suggest this?"**

Every UTF action must be traceable to:
- Which rules/patterns triggered it
- What data informed the decision
- How confidence was calculated
- Audit log entry for the suggestion

### 3. Token Efficiency
- UTF should NOT be used for routine operations
- Deterministic automation preferred where possible
- UTF triggers only for:
  - Ambiguous user requests
  - Cross-module insights
  - Novel pattern detection
  - User-requested AI features

### 4. Local-First Privacy
- UTF may use external LLM APIs ONLY if user explicitly configures
- All sensitive data processing happens locally
- Anonymization required before any external API calls
- User must opt-in to any cloud features

---

## Implementation Guidelines for Codex

### When to Build UTF Features
**NOT NOW.** UTF is deferred until core modules are stable.

Check `.claude/FEATURES.md` - if no UTF tasks are in "Next" section, do NOT implement UTF features.

### If/When UTF Task Appears in FEATURES.md

1. **Read First:**
   - This file (ATLAS_UTF_LENS.md)
   - `.claude/WORKING_NOTES.md` (coordination rules)
   - Core module interfaces being enhanced

2. **Architecture Pattern:**
   ```python
   # utf/task_coordinator.py
   from modules.core.task_tracker import TaskTracker  # ✅ UTF imports core

   class UTFTaskCoordinator:
       def __init__(self, task_tracker: TaskTracker):
           self.core = task_tracker  # Composition, not inheritance

       def suggest_next_task(self) -> dict:
           """Suggest task using AI, return explanation."""
           tasks = self.core.list_tasks()  # Use core APIs
           # UTF logic here
           return {
               'task': suggested_task,
               'reason': 'explanation',
               'confidence': 0.85,
               'audit_id': 'UTF-2026-...'
           }
   ```

3. **Testing UTF Features:**
   - Test core functionality WITHOUT UTF (must pass)
   - Test UTF enhancement layer separately
   - Test graceful degradation if UTF unavailable
   - Test explainability (can system explain its suggestions?)

4. **Configuration Pattern:**
   ```python
   # config/utf_config.yaml (user must create to enable)
   utf:
     enabled: false  # Default: disabled
     llm_provider: null  # Options: null, 'openai', 'anthropic', 'local'
     api_key: null
     features:
       task_suggestions: false
       content_generation: false
       natural_language_queries: false
   ```

---

## UTF vs Core Decision Tree

**Use Core (deterministic automation):**
- ✅ Adding tasks to database
- ✅ Fetching stock prices on schedule
- ✅ Tracking habits/goals
- ✅ Managing contacts
- ✅ Exporting data to CSV/JSON

**Use UTF (intelligent overlay):**
- ❌ NOT YET - deferred post-MVP
- 🔮 Future: "What should I work on next?" (cross-module priority)
- 🔮 Future: "Summarize my week's progress" (natural language reports)
- 🔮 Future: Video script generation from content ideas
- 🔮 Future: Anomaly detection in financial data

---

## Handoff Protocol for UTF Work

When implementing UTF features, append to `.claude/WORKING_NOTES.md`:

```markdown
### [YYYY-MM-DD HH:MM] CODEX -> CLAUDE (UTF Feature: [Name])
**Files Changed**
- UTF/[module_name].py
- tests/test_utf_[module].py
- config/utf_config.yaml (template)

**Explainability Evidence**
- [ ] UTF can explain why it made each suggestion
- [ ] Audit log captures all UTF actions
- [ ] User can disable UTF without breaking core

**Degradation Test**
- [ ] Core module works with UTF disabled
- [ ] UTF failure doesn't crash core functionality

**Proposals/Decisions Needed**
- [Any architecture questions for Claude]
```

---

## Current Status: NOT IMPLEMENTED

UTF is a future enhancement. Focus on core modules first:
- ✅ CORE-001, CORE-002, CORE-003 (Complete)
- ✅ LIFE-001, LIFE-002 (Complete)
- ✅ FIN-001, FIN-002 (Complete)
- 🔄 Next: Content & Knowledge Management modules

**Do not implement UTF features unless explicitly listed in `.claude/FEATURES.md` "Next" section.**

---

## Questions for Claude (PM)?

If you encounter UTF-related ambiguity during implementation:

1. Does this feature require UTF, or can core modules handle it deterministically?
2. How should we balance explainability vs. feature complexity?
3. What's the minimum viable UTF feature set?
4. Should UTF have its own database tables, or only augment queries?

**Append questions to `.claude/WORKING_NOTES.md` - do NOT edit planning files directly.**

---

**Last Updated:** 2026-01-20
**Maintained By:** Claude (PM/Steward)
**Audience:** Codex (Builder Agent)
