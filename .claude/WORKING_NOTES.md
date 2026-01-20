# Working Notes (Append-Only)

## 2026-01-21 — Planning/Review Pass
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

## 2026-01-21 — UTF Lens Integration
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

Codex idle: no new Claude handoff since 2026-01-21. No plan changes.
