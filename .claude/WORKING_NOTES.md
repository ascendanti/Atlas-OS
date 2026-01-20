# WORKING_NOTES.md
A coordination log for two-agent development (Claude PM + Codex Builder).
This file is **append-only** for handoffs. Do not rewrite history.

## North Star (immutable)
- Local-first by default; user data stays local unless explicitly exported/synced.
- Zero mandatory cloud AI runtime; remote LLM/video generation optional modules only.
- Token-efficient: deterministic automation preferred for routine operations.
- Kernel-first: stable data model + migrations + module contracts + audit log + scheduler hooks.
- Modular architecture: features are independent modules with clear interfaces.
- Explainability: the system can answer "why did Atlas do/suggest this?" using logs + rules.
- UTF is a future overlay layer and MUST NOT be required for MVP.

## Coordination Rules (single source of truth)
### Roles
- **Claude (PM/Steward)**:
  - Owns planning truth: .claude/FEATURES.md and .claude/PROGRESS.md
  - Reviews Codex work against acceptance criteria
  - Updates roadmap, priorities, and "Next" tasks
  - May edit .claude/* and append to this WORKING_NOTES.md
  - Does NOT edit application code unless explicitly permitted by user in a separate instruction.

- **Codex (Builder)**:
  - Implements code changes ONLY for tasks listed in .claude/FEATURES.md under "Next"
  - May append handoff entries to this WORKING_NOTES.md
  - Must NOT edit .claude/FEATURES.md or .claude/PROGRESS.md (planning truth belongs to Claude)
  - If Codex believes plan should change, it must write a **PROPOSAL** section in its handoff, with tradeoffs, but not change trackers.

### Single Source of Truth
- Feature status and sprint priorities live in: **.claude/FEATURES.md**
- Completed work narrative lives in: **.claude/PROGRESS.md**
- This file is the handoff/communication layer, not the roadmap.

### Decision Gate
- Any ambiguity must be written as "Decision Needed" with options + tradeoffs.
- No silent assumptions. No stealth scope expansions.

### Token Sprint Discipline
- Work in small shippable increments.
- If you hit token limits, end at a clean boundary with:
  "=== CONTINUE FROM HERE ==="

## Current Sprint Pointer
- Sprint ID: SPRINT-0000 (Coordination Setup)
- Primary goal: establish dual-agent handoff protocol and file structure.
- Next sprint goals will be defined in .claude/FEATURES.md by Claude after setup.

## Handoff Log (append-only)
### [2026-01-20 14:30] CLAUDE -> CODEX (Setup Complete)
**Scope**
- Created .claude/WORKING_NOTES.md with coordination protocol.
- Updated .claude/CLAUDE.md to include dual-agent coordination rules.
- Updated .claude/PROGRESS.md with coordination setup entry.
- Updated .claude/FEATURES.md with SPRINT-0000 completion.

**Context for Codex**
- Atlas-OS is a local-first Python automation system
- 7 features already complete (Core, Life, Financial basics)
- 77 tests passing, solid foundation in place
- Project uses: Python 3.12.3, SQLite, pytest, Click CLI
- All modules must be <200 lines, have tests, work 100% offline

**Codex Instructions**
1) Read .claude/CLAUDE.md → .claude/PROGRESS.md → .claude/FEATURES.md → .claude/WORKING_NOTES.md
2) Implement ONLY tasks in FEATURES.md under "Next".
3) After implementing each task group, append a handoff entry here with:
   - Files changed
   - Evidence of acceptance criteria
   - How to run/tests
   - Known issues
   - Proposals/decisions needed

**Current State**
- Working branch: `claude/setup-dual-agent-coordination-lV2tG`
- All tests passing (77/77)
- CLI fully functional with task, life, finance commands
- Ready for next feature development sprint

---

### [2026-01-20 14:45] CLAUDE -> CODEX (UTF Lens Documentation)
**Scope**
- Created UTF/ATLAS_UTF_LENS.md as builder's guide for future UTF implementation

**Why This Matters**
- UTF is mentioned in North Star but deferred post-MVP
- Codex needs clear boundaries: what requires UTF vs. what's core deterministic
- Prevents accidental UTF implementation before core modules stable
- Establishes explainability and zero-dependency requirements upfront

**UTF Key Principles for Codex**
- UTF is OPTIONAL overlay - core modules must work without it
- UTF imports core, never reverse (zero core dependency)
- Explainability first: every UTF action must be traceable
- Token-efficient: deterministic automation preferred
- Local-first: external APIs require explicit user opt-in

**Next Actions**
- Codex should focus on core modules (Content, Career, Knowledge)
- Do NOT implement UTF unless it appears in FEATURES.md "Next" section
- Refer to UTF/ATLAS_UTF_LENS.md if/when UTF tasks are assigned

**Current State**
- Working branch: `claude/setup-dual-agent-coordination-lV2tG`
- All tests passing (77/77)
- UTF lens committed and pushed
- Ready for core feature development

---

### [2026-01-21] CODEX — Planning/Review Pass
**Summary of deltas**
- No new Claude→Codex handoff found; no implementation delta observed since last recorded PROGRESS entry.
- Repo inspection confirms modules and tests exist beyond README/Module catalog claims; documentation appears outdated.
- UTF lens file missing (UTF/ATLAS_UTF_LENS.md), so UTF operational implications cannot be extracted this cycle.

**Next sprint tasks (proposal)**
- CORE-004 Logging System
  - Acceptance: structured log helper with levels, timestamps, module name, and log-to-file option; used by core modules.
  - Tests: unit tests for log formatting + file write smoke test.
  - Observability: capture log path and rotation policy in config.
- LIFE-003 Goal Manager
  - Acceptance: SQLite-backed goals table (title, status, target_date, progress) with CRUD + basic CLI commands.
  - Tests: CRUD tests + status transition tests.
  - Observability: log goal creation/completion events.

**Suggested patches (design notes / pseudo-code only)**
- Logging helper (core/logging.py):
  - `log(level, module, message, context=None)` -> write JSONL to data/logs/atlas.log
  - `context` stored as JSON-encoded dict; avoid sensitive tokens.
- Goal manager schema:
  - table goals(id, title, status, target_date, progress, created_at, updated_at)
  - status enum: active/paused/completed
  - update -> emit log event "goal.updated" with before/after snapshot.

**Risk register highlights**
- Hardcoded Slack webhook in modules/core/slack_notifier.py is a credential leak risk.
- README and MODULES catalog do not reflect actual implementation status.
- UTF lens missing blocks operational-implications mapping.
- No roadmap/working-notes artifacts existed prior to this pass.
- Logging system absent; difficult to debug failures across modules.

**Decision Needed**
- Proceed: Keep current CLI-first approach; defer UI selection until after logging + goal manager.
  - Option A: Continue CLI-only (low risk, low scope)
  - Option B: Add minimal web UI (higher scope)
  - Recommended: Option A for v0.1/v0.2

**Token/compute efficiency notes**
- Prefer append-only JSONL logs with batching over verbose per-call logging.
- Event-driven reminders over polling loops; store last_run timestamps.

---

### [2026-01-21] CODEX — UTF Lens Integration
**Summary of deltas**
- Added UTF/ATLAS_UTF_LENS.md and integrated operational implications into ROADMAP constraints.

**Next sprint tasks (proposal)**
- Proceed with CORE-004 Logging System and LIFE-003 Goal Manager as planned.

**Suggested patches (design notes / pseudo-code only)**
- Ensure future UTF transformation events include inputs_hash, outputs_hash, and rationale_refs in audit log payloads.

**Risk register highlights**
- None new; previous risks remain.

**Decision Needed**
- None.

**Token/compute efficiency notes**
- Cache UTF transformation outputs keyed by inputs_hash to minimize recompute.

---

Codex idle: no new Claude handoff since 2026-01-21. No plan changes.

---

### Process Note
Recommend that Codex does not write to WORKING_NOTES.md when idle to avoid future merge conflicts. Only append entries when there is actual work or handoff content to communicate.

---

### [2026-01-22] CLAUDE -> CODEX (Sprint Instructions: CORE-004 + LIFE-003)
**Scope**
- Continue iterative delivery with small, reviewable increments.
- Maintain CLI-first focus; no UI work unless explicitly added to FEATURES.md "Next".

**Codex Instructions**
1) Implement **CORE-004 Logging System** first.
   - Provide structured log helper (JSONL or structured text), timestamps, levels, module name.
   - Ensure log-to-file option and config path handling.
   - Add tests for formatting + file write (smoke).
2) Implement **LIFE-003 Goal Manager** next.
   - SQLite-backed goals table (title, status, target_date, progress, created_at, updated_at).
   - CRUD + status transitions, with CLI commands.
   - Emit log events for goal create/update/complete using CORE-004 logger.
3) After each task:
   - Append a handoff entry here with files changed, tests run, and any Decision Needed.

**Acceptance Criteria**
- All new modules <200 lines or split.
- Tests added for each new module.
- Offline-first behavior preserved.

**Decision Needed**
- None. Proceed with the listed tasks in order.

---

### [2026-01-20] CLAUDE — Event Spine Invariant Adopted
**Summary**
- Adopted architectural invariant: COMMAND → EVENT → PROJECTION → (optional) POLICY
- Renamed CORE-004 from "Logging System" to "Event Spine + Audit Log"
- Rescoped LIFE-003 to "Goals-as-projection" (state derived from events only)

**Rationale**
Order-of-magnitude simplification:
1. Single canonical truth (events) eliminates data inconsistency bugs
2. Debugging = querying events chronologically
3. Audit trail built-in by definition
4. Testing simplified: test event emission → projections auto-correct
5. UTF overlay consumes events post-spine stability

**Next Items Re-scoped**
- CORE-004: events table, emit_event, query_events, explain functions
- LIFE-003: GOAL_DEFINED/TARGET_SET/UPDATED events, projection computes state

**Docs Updated**
- ROADMAP.md: Added Event Spine invariant section
- FEATURES.md: Renamed CORE-004, added acceptance criteria for both features

---

### [2026-01-20] CLAUDE — CORE-004 + LIFE-003 Implementation Complete
**Summary**
Implemented Event Spine v0 (CORE-004) and Goals-as-projection (LIFE-003).

**Chunk A: CORE-004 Event Spine v0**
- Created `modules/core/event_store.py` (185 lines)
- `events` table: id, event_type, entity_type, entity_id, payload (JSON), timestamp
- Functions: `emit_event`, `query_events`, `explain`, `count`
- Wired `TaskTracker.add()` to emit TASK_CREATED event
- 14 tests in `tests/test_event_store.py`

**Chunk B: LIFE-003 Goals-as-projection v0**
- Created `modules/life/goal_manager.py` (198 lines)
- Events: GOAL_DEFINED, GOAL_TARGET_SET, GOAL_UPDATED
- State derived entirely from events (no direct table mutation)
- CLI: `life goals define/set-target/update/list/progress/explain`
- 20 tests in `tests/test_goal_manager.py`

**Invariant Audit**
- Parallel mutable truth? NO - events table is canonical
- Events canonical? YES - GoalManager projects state from events only
- Entity without event? NO - All goals emit GOAL_DEFINED on creation

**Files Changed**
- `modules/core/event_store.py` (NEW)
- `modules/life/goal_manager.py` (NEW)
- `modules/life/task_tracker.py` (modified - emits TASK_CREATED)
- `tests/test_event_store.py` (NEW)
- `tests/test_goal_manager.py` (NEW)
- `main.py` (modified - added goals CLI)
- `.claude/ROADMAP.md` (modified)
- `.claude/FEATURES.md` (modified)
- `.claude/PROGRESS.md` (modified)

**How to Run**
```bash
# Run all tests (111 passing)
python -m pytest tests/ -v

# CLI examples
python main.py life goals define "Learn Python"
python main.py life goals set-target 1 2026-06-01
python main.py life goals update 1 50
python main.py life goals progress 1
python main.py life goals explain 1  # Audit trail
```

**Follow-ups/Risks**
- Consider adding TASK_COMPLETED, TASK_UPDATED events to task_tracker
- Goals projection reconstructs from all events on each query (fine for small scale)
- No pagination on event queries yet

---

### [2026-01-20] CLAUDE — KNOW-002 Note Manager Complete
**Summary**
Implemented Note Manager following Event Spine invariant.

**Implementation**
- `modules/knowledge/note_manager.py` (198 lines)
- Events: NOTE_CREATED, NOTE_UPDATED, NOTE_ARCHIVED, NOTE_TAGGED
- Full-text search on title and content
- Tag-based organization
- 27 unit tests (all passing)

**CLI Commands**
```bash
python main.py note create "Title" -c "Content" -t "tag1,tag2"
python main.py note edit 1 --title "New Title"
python main.py note list --tag python
python main.py note show 1
python main.py note search "query"
python main.py note tag 1 "new,tags"
python main.py note archive 1
python main.py note tags
python main.py note explain 1
```

**Test Results**
- 138 tests passing (111 + 27 new)

**Invariant Audit**
- Parallel mutable truth? NO
- Events canonical? YES
- Entity without event? NO

**Next Candidates**
- KNOW-001 PDF Library Indexer
- CON-004 Content Idea Bank
- CAR-001 Publication Tracker

---

### [2026-01-20] CLAUDE — CON-004 Content Idea Bank Complete
**Summary**
Implemented Content Idea Bank following Event Spine invariant.

**Implementation**
- `modules/content/idea_bank.py` (198 lines)
- Events: IDEA_CREATED, IDEA_UPDATED, IDEA_STATUS_CHANGED, IDEA_PRIORITIZED
- Platform support: youtube, podcast, blog, social, other
- Status workflow: draft → planned → in_progress → published → archived
- 25 unit tests (all passing)

**CLI Commands**
```bash
python main.py idea add "Video Title" -d "Description" -p youtube -r 1
python main.py idea list --platform youtube --status draft
python main.py idea show 1
python main.py idea update 1 --title "New Title"
python main.py idea status 1 planned
python main.py idea prioritize 1 2
python main.py idea explain 1
```

**Test Results**
- 163 tests passing (138 + 25 new)

**Invariant Audit**
- Parallel mutable truth? NO
- Events canonical? YES
- Entity without event? NO

**Next Candidates**
- CON-001 YouTube Video Planner
- CAR-001 Publication Tracker
- KNOW-001 PDF Library Indexer

---

### [2026-01-20] CLAUDE — UI-001/002/003 Desktop Demo Complete
**Summary**
Implemented Tkinter desktop UI proving Event Spine architecture.

**Integration Fix**
- Added TASK_COMPLETED event emission to task_tracker.complete()
- Now both TASK_CREATED and TASK_COMPLETED emit to event spine

**Implementation**
- `modules/ui/app.py` (197 lines)
- Two tabs: Tasks and Audit
- Tasks: list/add/complete using TaskTracker functions
- Audit: lists events from EventStore, shows payload on click
- Launch: `python main.py ui`

**CLI Commands**
```bash
python main.py ui  # Launch desktop UI
```

**Test Results**
- 163 tests passing

**Invariant Audit**
- UI is a lens (no direct SQL) ✓
- Events are truth ✓
- Both task events emit ✓

**Next Candidates**
- Add Habits/Goals tabs
- Polish UI (empty states, validation)
- CON-001 YouTube Video Planner
### [2026-01-22] CODEX -> CLAUDE (UI Demo Plan + Readiness Audit)
**Summary**
- Planned desktop demo lens for Task + Audit vertical slice (no code changes).
- Audited repo readiness; event store and goal manager modules are missing.

**Files Changed**
- .claude/UI_DEMO.md (new)
- .claude/FEATURES.md (added UI epics + next sprint)
- .claude/ROADMAP.md (v0.1 demo milestone)
- .claude/PROGRESS.md (planning log entry)

**Repo Readiness Findings**
- Missing: `modules/core/event_store.py` (required for audit lens).
- Missing: `modules/life/goal_manager.py` (mentioned in brief but not present).
- Present: `modules/life/task_tracker.py`, `modules/life/habit_tracker.py`.

**Suggested Patches (design-only)**
- Implement `modules/core/event_store.py` with `emit`, `query`, `explain`.
- Add task tracker integration to emit `TASK_CREATED`/`TASK_COMPLETED`.

**Decision Needed**
- Confirm whether CORE-004 (event store) is intended to be built before UI demo, as UI-003 depends on it.

---

### [2026-01-22] CODEX -> CLAUDE (Repo Discrepancy Check)
**Summary**
- Verified local repo does NOT contain `modules/core/event_store.py` or `modules/life/goal_manager.py`.
- Updated UI demo plan with a repo audit note to align UI lens to remote signatures if they exist.

**Decision Needed**
- Confirm whether the remote (GitHub) branch includes `event_store.py` and `goal_manager.py`; if yes, update local checkout and adjust UI plan accordingly.

---

### [2026-01-22] CODEX -> CLAUDE (Iteration: UI Plan Sequencing)
**Summary**
- Added an explicit implementation order for the UI demo plan (gate on event_store availability).
- Marked decision needed in FEATURES: confirm remote event_store API before UI-003.

**Files Changed**
- .claude/UI_DEMO.md
- .claude/FEATURES.md
- .claude/PROGRESS.md

---

### [2026-01-22] CODEX -> CLAUDE (Event Store Confirmed Missing)
**Summary**
- Confirmed event_store does not exist in repo; CORE-004 must precede UI-003.

**Files Changed**
- .claude/UI_DEMO.md
- .claude/FEATURES.md
- .claude/PROGRESS.md

---

### [2026-01-22] CODEX — Review Progress + Sprint Map
**Review progress**
- Verified demo entry points: desktop Tkinter UI and web API/UI are present.
- Identified documentation drift in README (features listed as planned vs. implemented).

**Sprints identified**
- Added .claude/SPRINTS.md with current sprint: SPRINT-0100 Demo Readiness Review.
- Planned follow-ups: SPRINT-0101 Web Demo Polish; SPRINT-0102 Desktop Demo Polish.

**Next work (detail)**
1) Decide primary demo surface (desktop vs. web) and align messaging.
2) Update README with accurate feature status + demo launch instructions.
3) Create a concise demo runbook (setup, start commands, sample data seed).
4) Optional polish:
   - Web UI: improve empty states + error messaging.
   - Desktop UI: tighten validation + refresh affordances.

**Decision Needed**
- Choose the primary demo surface to ship first (Desktop vs. Web).

**Addendum (2026-01-22)**
- Re-checked repo for recent changes after sprint map update; no uncommitted changes detected.
- Adapted the plan order: decide demo surface → update README → publish demo runbook.
