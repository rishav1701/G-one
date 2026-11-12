# API

The FastAPI OpenAPI export is [openapi.json](api/openapi.json). The running API also serves interactive documentation at `/docs` and the schema at `/api/v1/openapi.json`.

All application routes are under `/api/v1`. Session authentication uses an HttpOnly session cookie; browser mutations require the CSRF header. The simulator ingestion route uses a separate hashed `X-API-Key` with the `ingest:write` scope. Non-admin clinical access is ward-scoped, and out-of-scope records return 404.

## Route groups

- `/auth`: CSRF challenge, login, current session, logout, password change, and local-demo status/sign-in. The optional `/auth/demo-login` accepts only `account: clinician` or `account: admin`; it is enabled only in development for localhost requests and creates an audited server-side session without returning a password.
- `/admissions`, `/patients`, `/observations`: scoped worklist/detail reads, single and batch observation ingestion, risk assessments and explanations.
- `/alerts`: alert list and lifecycle actions, response history, and escalation details.
- `/admin`: user and ward management, operational configuration, system status, audit events, simulator reset and simulated clock controls.
- `/analytics`: request-time operational figures and demonstration scenario summaries.
- `/admissions/{id}/labs`: scoped read-only synthetic lab results.
- `/admissions/{id}/model-predictions`: predictions only when a verified active model exists.
- `/health`: database connectivity check used by the local deployment.

The schema is generated from the current FastAPI application. Regenerate it after API contract changes with:

```powershell
Set-Location backend
..\.tools\python311\python.exe -c "import json; from app.main import app; open('../docs/api/openapi.json','w',encoding='utf-8').write(json.dumps(app.openapi(),indent=2)+'\\n')"
```
