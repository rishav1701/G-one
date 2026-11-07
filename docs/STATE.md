# Project state

- Current phase: Phase 8 complete; release checkpoint v0.1.0.
- Completed: Phases 0–8. Phase 8 adds a local Compose stack, generated environment secrets, setup/seed/reset/demo scripts, and the complete documentation set. The clean-clone local installation and demo passed; Docker runtime remains UNVERIFIED because the Desktop engine did not respond to the CLI.
- Product gates: Phases 1–7 passed. Phase 8 packaging configuration and clean local clone passed; container build/start is UNVERIFIED. Evidence is in `docs/reports/phase-8.md`.
- Track B status: the G One ward feature-contract pipeline remains fixture-tested. A separate PhysioNet 2019 ICU sepsis research candidate was trained, evaluated on a patient-grouped holdout, and packaged with attribution under `models/research/`; it is explicitly unaccepted and inactive. Full source data remains local in ignored `.tools/`; no credentialed data was used.
- Open risks: Docker image build and Compose startup remain UNVERIFIED. The ICU sepsis candidate has low PPV (2.75% at its validation-selected exploratory threshold), is uncalibrated, and is not compatible with the ward NEWS2 contract. A qualified clinician must review NEWS2 before any clinical use. The system is a simulated demonstration, not for clinical use.
- Open dependency risk: none found by the completed npm and pip audits. Docker Compose and clinician review remain pending.
- Last checkpoint: Phase 8 clean-clone install, migrations, seed, six-scenario demo, local API/UI start, and browser login passed. `docker compose config --quiet` passed; the Docker Desktop engine did not answer `docker info` or `docker version`, so image build and Compose runtime must be verified on a working Docker host.
