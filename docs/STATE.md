# Project state

- Current phase: Phase 2 complete; Phase 3 is next.
- Completed: Phase 0 reconnaissance/planning; Phase 1 security foundation and UI gate; Phase 2 NEWS2 engine, PostgreSQL clinical schema, single-observation ingestion, ward-scoped clinical reads, persisted/reproducible assessments, and NEWS2 100% branch-coverage gate.
- Product code: Phase 1 and Phase 2 gates passed. Evidence is in docs/reports/phase-1.md and docs/reports/phase-2.md. Clinical scoring comparison and review notice are in docs/CLINICAL_METHODOLOGY.md.
- Open risks: Docker Desktop engine is unavailable; Phases 1 and 2 were verified with a local PostgreSQL 17.11 cluster and portable Python runtime under ignored .tools. A qualified clinician must still verify the NEWS2 implementation before any clinical use. gitleaks availability remains unverified for hardening.
- Track B: pending user M0 data decision and later user-run local training. Neither blocks the application.
- Last checkpoint: Phase 2 gate changes are ready to commit.
