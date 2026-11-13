# Login navigation fix — 2026-11-13

## Delivered

- Protected the authenticated user state from a late initial `/auth/me` response after login starts.
- Login completion now clears the startup loading state; an older session-check response cannot replace the login result.
- Added a regression test that delays and then rejects `/auth/me` after a successful login.

## Gate results

- `npm test -- --run` (from `frontend/`) — passed, 22 tests across 6 files.
- `npm run build` (from `frontend/`) — passed, including TypeScript compilation and Vite bundle.

## UNVERIFIED

- A live browser login and PostgreSQL-backed dashboard load. Docker Desktop's engine is unavailable in this session.

## Decision

- Auth state changes use a monotonically increasing revision so stale initial session requests cannot overwrite a newer login or logout action.

## Deviations and cuts

- No features were cut. Live runtime validation could not be performed without Docker.

## Known defects and next prerequisite

- No defect found in frontend tests. With Docker Desktop running, rebuild the backend and frontend with `docker compose up -d --build`, then sign in and verify the dashboard data loads.
