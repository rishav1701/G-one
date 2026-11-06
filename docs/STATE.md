# Project state

- Current phase: Phase 5 complete; Phase 6 is next.
- Completed: Phases 0–5. Phase 5 adds alert actions and responses, administrator user/ward management, operational settings, system status, audit viewer, and deterministic simulator controls. UI review evidence and screenshots are in `docs/UI_REVIEW.md` and `docs/screens/phase-5/`.
- Product gates: Phase 1 UI/auth foundation, Phase 2 clinical core, Phase 3 assessment/alerts/simulator, Track B M1/M2 fixture pipeline, Phase 4 frontend core, and Phase 5 alert workflow/administration passed. Phase 5 evidence is in `docs/reports/phase-5.md`.
- Track B status: fixture-only pipeline and candidate artifact verified. The candidate is explicitly unaccepted and inactive. M0 data governance and later approved-data training remain pending and do not block application work.
- Open risks: Docker engine and Compose startup remain unverified. A qualified clinician must review NEWS2 before any clinical use. The system is a simulated demonstration, not for clinical use.
- Open dependency risk: `npm install` reported 9 audit findings (1 moderate, 6 high, 2 critical); review and remediate in Phase 7 without blind upgrades.
- Last checkpoint: Phase 5 gates passed, including the full browser workflow and zero serious/critical axe violations; proceed to Phase 6 analytics, labs, and model integration.
