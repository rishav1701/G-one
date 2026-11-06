# Database

G One uses PostgreSQL and applies migrations through Alembic. The backend startup command runs `alembic upgrade head` before starting Uvicorn. No application startup path calls `Base.metadata.create_all`.

## Tables

| Table | Purpose |
|---|---|
| `ward` | Ward scope for users, admissions, and data-source status. |
| `app_user`, `user_ward`, `session` | Argon2id password hashes, role and ward assignments, and hashed opaque sessions with expiry. |
| `api_key` | Hashed simulator ingestion key with a fixed write scope. |
| `patient`, `admission` | Synthetic patient identifier, age and sex; ward placement, SpO₂ scale, simulation label and scenario. |
| `observation`, `ingestion_rejection` | Immutable accepted measurements with idempotency fields, and rejection metadata that does not persist rejected payload values. |
| `lab_result` | Read-only, simulated lab values. Labs do not affect NEWS2 or model inference. |
| `risk_assessment` | Versioned NEWS2 score, parameter breakdown, completeness, timestamps and observation references. |
| `alert`, `alert_event`, `clinical_response`, `escalation` | Alert state, append-only workflow history, structured clinical response, and in-app demonstration escalation. |
| `data_source_status`, `system_config` | Simulator source connectivity and operational demonstration settings. |
| `model_prediction` | A calibrated prediction linked to an assessment, model version and feature hash; shown only for a verified active artifact. |
| `audit_log` | Append-only actor/action/object/request records. |

## Integrity and privacy

UUID-form identifiers are used internally; the UI displays synthetic `SIM-000001` identifiers. There are no names, dates of birth or addresses. Constraints protect unique idempotency keys, one current open alert per admission, probability bounds, allowed states, and foreign-key consistency. Timestamps are PostgreSQL `timestamptz` and are stored in UTC. Audit rows reject updates and deletes.

## Migrations

The ordered migrations are in `backend/alembic/versions/`. Check the current revision with `alembic current` and apply updates with `alembic upgrade head` from `backend/`.
