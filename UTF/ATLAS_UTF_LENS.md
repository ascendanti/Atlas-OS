# Atlas UTF Lens

## Purpose
This document defines the UTF (Unified Transformation Framework) lens and its operational implications for Atlas. It informs constraints and sequencing but does not replace the main roadmap.

## Operational Implications
- **Local-first computation**: UTF transformations must run locally by default; remote services are optional and modular.
- **Auditability**: Every UTF transformation must emit an event in the audit log with inputs, outputs, and rationale metadata.
- **Token efficiency**: Prefer deterministic transforms and cached results; avoid repeated expensive calls.
- **Explainability**: Every recommendation must provide a human-readable "why" tied to source events.
- **Scheduling**: UTF jobs should be event-driven where possible; avoid frequent polling.

## Kernel Requirements (Mapped)
- Event log supports UTF transformation events with structured payloads.
- Schema includes UTF state vectors and transformation metadata storage.
- Module registry supports declaring UTF transforms and dependencies.

## Observability & Tests
- Log transformation start/end with duration and IO stats.
- Test: determinism check for given inputs; event log append-only verification.
- Test: explainability output includes event references.

## Backlog Guidance
- UTF layer should follow Kernel v1 and Background Ops v1 (M1/M3).
- Avoid UTF-driven features in MVP v0.1; introduce in later milestone (M7).
