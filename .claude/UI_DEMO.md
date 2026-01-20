# UI Demo Plan (Desktop Lens)

## Purpose
Deliver a minimal desktop demo that proves the Atlas paradigm shift:
**COMMAND → EVENT(S) → PROJECTION(S) → (optional) POLICY**.
This UI is a **lens layer** only: it must call existing module functions and read the canonical event store.

## Demo Narrative (Vertical Slice)
1) **Add Task** → emits `TASK_CREATED` event.
2) **Complete Task** → emits `TASK_COMPLETED` event.
3) **Audit tab** shows event stream and allows per-entity history.
4) (Optional next) show projection changes for Habits/Goals after tasks are updated.

## Information Architecture (IA)
Tabs (Notebook UI):
- **Today** (stub)
- **Tasks** (implemented v0)
- **Habits** (stub)
- **Goals** (stub)
- **Audit** (implemented v0)

## Interaction Grammar
- **List**: table/grid with sort + filter
- **Detail**: selected entity details + quick actions
- **Command Bar**: quick-add actions (future extension)

### Minimal Command Bar Contract (v0)
- `task add "<title>"` → opens add dialog or inline form
- `task complete <id>` → completes selected task
- `audit show <entity> <id>` → filters audit view

## Audit Lens Requirements
- **Event listing**: timestamp, type, entity, payload
- **Filters**: by event type, entity type, entity id
- **Explain**: per-entity history (chronological)
- **Payload view**: JSON pretty-print

## Mapping to Code (Suggested Patches Only)
**UI entry point (lens only):**
- Recommended path: `ui/desktop_app.py` (or `atlas_ui.py` at repo root)
- UI must call module functions; no SQL in UI.

**Modules to call:**
- `modules.life.task_tracker.TaskTracker.add(...)`
- `modules.life.task_tracker.TaskTracker.complete(...)`
- `modules.life.task_tracker.TaskTracker.list(...)`
- `modules.core.event_store.EventStore.emit(...)`
- `modules.core.event_store.EventStore.query(...)`
- `modules.core.event_store.EventStore.explain(entity_type, entity_id)`

**Repository audit note:**
- Local checkout does not currently include `modules/core/event_store.py` or `modules/life/goal_manager.py`.
- If these exist on remote, align the UI lens to their actual function signatures; otherwise implement CORE-004 before UI-003.

**Event emission contract (for integration proof):**
- On task creation: emit `TASK_CREATED` with payload `{task_id, title, priority, due_date}`.
- On task completion: emit `TASK_COMPLETED` with payload `{task_id, completed_at}`.

## Demo Success Criteria
- Can add a task via UI and see it appear in list.
- Can complete a task via UI and see status update.
- Audit tab shows both events with correct payloads and timestamps.
- UI does not write SQL or maintain parallel state.

## Constraints
- UI is **lens-only** (no new truth stores).
- Offline-first; uses local SQLite data already in `data/`.
- Keep scope minimal; no styling beyond clarity.
