# Roadmap

## Principles (Non-Negotiable)
1) Local-first by default
2) Zero mandatory cloud AI runtime (remote optional modules only)
3) Token-efficiency via deterministic automation
4) Coherence kernel: consistent schemas + event log / audit trail
5) Modular architecture with stable contracts
6) Explainability: "why did Atlas do/suggest this?"

## Milestones (Immutable Tail)
- M1) Kernel v1: unified data model + module registry + migrations + audit log + scheduler hooks
- M2) UX v1: local dashboard with module panels + global search + inbox triage
- M3) Background Ops v1: daemon mode + scheduled jobs + notifications (Windows-first)
- M4) Knowledge Spine v1: local indexing/search across artifacts (no cloud dependency)
- M5) Finance Spine v1: local portfolio/budget primitives + scheduled checks (API optional)
- M6) Social Ops v1: content calendar + posting pipelines + analytics aggregation (opt-in modular)
- M7) UTF Layer v1: state vectors + transformations from events + coherence scoring + explainable recommendations
- M8) Sync/Sharing v1 (Opt-in): encrypted export + privacy-preserving sharing primitives
- M9) G2M Readiness v1: packaging/installer + update mechanism + telemetry opt-in + support docs + SKU split

## Near-Term Releases
- v0.1 (Capture → Organize → Review): kernel schema + module registry + minimal CLI; no daemon.
- v0.2 (Background ops): scheduler + notifications + review loop polish.
- v0.3 (Power module): choose one spine (knowledge OR finance) based on repo readiness.

## UTF Operational Implications (Constraints)
- Local-first computation; remote UTF services optional only.
- Emit audit log events for every UTF transformation (inputs/outputs/rationale metadata).
- Favor deterministic transforms with caching for token efficiency.
- Require explainability: human-readable "why" with source event references.
- Prefer event-driven scheduling; avoid frequent polling loops.

## Decision Needed
- None
