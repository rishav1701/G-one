# Project state

- Current phase: Phase 6 complete; Phase 7 is next.
- Completed: Phases 0–6. Phase 6 adds database-backed analytics and scenario summaries, read-only synthetic lab results, and a fail-closed verified-model inference interface. UI review evidence and screenshots are in `docs/UI_REVIEW.md` and `docs/screens/phase-6/`.
- Product gates: Phase 1 UI/auth foundation, Phase 2 clinical core, Phase 3 assessment/alerts/simulator, Track B M1/M2 fixture pipeline, Phase 4 frontend core, Phase 5 alert workflow/administration, and Phase 6 analytics/labs/model integration passed. Phase 6 evidence is in `docs/reports/phase-6.md`.
- Track B status: fixture-only pipeline and candidate artifact verified. The candidate is explicitly unaccepted and inactive. M0 data governance and later approved-data training remain pending and do not block application work.
- Open risks: Docker engine and Compose startup remain unverified. A qualified clinician must review NEWS2 before any clinical use. The system is a simulated demonstration, not for clinical use.
- Open dependency risk: `npm install` reported 9 audit findings (1 moderate, 6 high, 2 critical); review and remediate in Phase 7 without blind upgrades.
- Last checkpoint: Phase 6 gates passed, including request-time metric verification, the no-model and test-fixture inference states, and zero serious/critical axe violations across the Phase 6 browser review. Proceed to Phase 7 hardening.
