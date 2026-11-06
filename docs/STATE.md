# Project state

- Current phase: Phase 7 complete; Phase 8 is next.
- Completed: Phases 0–7. Phase 7 hardens dependency pins, removes committed E2E passwords, improves password-change confirmation, and completes the scenario and UI audits. Security review is in `docs/SECURITY.md`.
- Product gates: Phase 1 UI/auth foundation, Phase 2 clinical core, Phase 3 assessment/alerts/simulator, Track B M1/M2 fixture pipeline, Phase 4 frontend core, Phase 5 alert workflow/administration, Phase 6 analytics/labs/model integration, and Phase 7 hardening passed. Phase 7 evidence is in `docs/reports/phase-7.md`.
- Track B status: fixture-only pipeline and candidate artifact verified. The candidate is explicitly unaccepted and inactive. M0 data governance and later approved-data training remain pending and do not block application work.
- Open risks: Docker engine and Compose startup remain unverified. A qualified clinician must review NEWS2 before any clinical use. The system is a simulated demonstration, not for clinical use.
- Open dependency risk: none found by the completed npm and pip audits. Docker Compose and clinician review remain pending.
- Last checkpoint: Phase 7 hardening passed: all 79 backend and 18 frontend tests, all six Playwright tests, 51 axe route/viewport checks, zero npm/pip advisories, and a clean known-key grep. Proceed to Phase 8 packaging and release.
