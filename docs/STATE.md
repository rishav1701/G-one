# Project state

- Current phase: Phase 3 complete; Phase 4 is next.
- Completed: Phases 0–3. Phase 3 includes persisted freshness-aware assessments, alert lifecycle and escalation, append-only audit events, operational settings, and a deterministic six-scenario simulator with at least 12 synthetic patients across two wards.
- Product gates: Phase 1 UI/auth foundation, Phase 2 clinical core, Phase 3 assessment/alerts/simulator, and Track B M1/M2 fixture pipeline gates passed. Evidence is in `docs/reports/phase-1.md`, `docs/reports/phase-2.md`, and `docs/reports/phase-3.md`.
- Track B status: fixture-only pipeline and candidate artifact verified. The candidate is explicitly unaccepted and inactive. M0 data governance and later approved-data training remain pending and do not block application work.
- Open risks: Docker engine and Compose startup remain unverified. A qualified clinician must review NEWS2 before any clinical use. The system is a simulated demonstration, not for clinical use.
- Last checkpoint: Phase 3 and Track B M1/M2 gates passed; proceed to Phase 4 frontend core.
