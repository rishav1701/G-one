# Release Notes — G One v0.1.0

## Release state

This release contains the Phase 0–8 simulated demonstration implementation. The shipped model state is **no trained ML model deployed**. No fixture candidate or test artifact is active.

## Included

- PostgreSQL-backed authentication, ward scoping, audit, observations, deterministic NEWS2 assessments, and alert workflow.
- Deterministic six-scenario simulator with synthetic patients and simulated lab results.
- Dashboard, patient directory/detail, alert centre, administration, analytics, and fail-closed model interface.
- Local Docker Compose packaging files and PowerShell setup, seed, reset, and demo scripts.

## Known limitations

- Not for clinical use. NEWS2 requires qualified local clinician review against the official chart and escalation policy.
- No real-data model is trained or deployed. Synthetic metrics and simulator outcomes are not clinical-performance evidence.
- Compose runtime and clean-clone container execution remain unverified in this environment because the Docker Desktop engine did not respond to the CLI.
- No production TLS, backup, high-availability, paging, or hospital device integration is configured.

## Verification

See `docs/reports/phase-8.md` for exact commands, results, and all unverified items. `v0.1.0` is a demonstration release identifier, not a clinical or regulatory approval claim.
