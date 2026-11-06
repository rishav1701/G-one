# Future work

G One is a simulated software demonstration, not for clinical use. NEWS2 requires qualified local clinical review before any clinical deployment. The ML candidate in `models/candidate/` was built on generated software fixtures, is explicitly unaccepted, and is not loaded by the application.

## Model work still required

- Complete `docs/DATA_DECISION_RECORD.md` with the dataset, provenance, cohort, event definition, observation protocol, prediction horizon, and acceptance criteria before any real-data training.
- Review and comply with the current dataset terms locally. Credentialed patient-level data must not be read by this agent or committed to this repository.
- Run a locally authorized, leak-checked training and evaluation process on an appropriate cohort. Provide only aggregate metrics and the manifest for review.
- Assess population mismatch, missingness, label noise, calibration, subgroup performance, prospective validation, local clinical review, and regulatory obligations. Synthetic-scenario results are demonstrations of system behavior and must not be interpreted as clinical performance.
- Promote only a reviewed artifact whose manifest has `acceptance_passed: true` and whose file hashes and feature contract verify. The model remains secondary to NEWS2; it never replaces the NEWS2 badge or automatically drives clinical actions.

## Product work still open

- Docker Compose startup and clean-clone container packaging remain unverified because the local Docker Desktop engine did not return a server response.
- A qualified clinician must verify NEWS2 thresholds, missing-data behavior, labels, and local escalation language before any clinical use.
- Release-hosted TLS, backups, operational monitoring, and paging integration are outside this local demonstration.
