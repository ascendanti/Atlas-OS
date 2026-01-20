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
