# Phase 1 report — Foundation, security spine, design system

## Delivered

- Added a FastAPI application, production secret guard, PostgreSQL connection setup, request ID/security-header middleware, and uniform API error envelopes.
- Added SQLAlchemy models and the initial Alembic migration for ward, app_user, user_ward, session, api_key, system_config, and audit_log.
- Added authentication routes with Argon2id password hashes, hashed opaque 256-bit session tokens, httpOnly SameSite=Lax cookies, pre-login and session CSRF checks, idle/absolute expiry, per-IP throttling, account lockout, password change, logout, and generated-password seeding.
- Added a deny-by-default session dependency, role dependency helper, route enumeration test, and backend security-spine test.
- Added the React/Vite/TypeScript frontend shell, persistent simulation banner, login form with show/hide password, auth context, CSRF-aware API client, route guard, shared UI components, Inter font dependency, design tokens, contrast/raw-value scripts, and a level badge test.
- Added a package lockfile. Generated node_modules are excluded from Git.

## Gate results

- Backend starts: UNVERIFIED — Python could not launch.
- Alembic migration applies to PostgreSQL: UNVERIFIED — Python and PostgreSQL unavailable; Docker daemon unreachable.
- Backend tests pass: UNVERIFIED — Python runtime unavailable.
- Frontend build and type-check: PASS — npm run build completed and Vite emitted the production bundle.
- Frontend tests: PASS — npm run test passed 2 files and 2 tests.
- Raw-value scan: PASS.
- Contrast check: PASS — body 17.85:1; secondary text 7.58:1.
- Login works in browser; wrong password, lockout, CSRF rejection, and expiry behave as specified: UNVERIFIED — no Playwright/Chromium and no runnable backend.
- UI gate for login and shell: UNVERIFIED — no Playwright/Chromium.

## Recovery attempts

- Initial npm installation did not make dependencies available immediately. A later reviewed installation populated node_modules and generated package-lock.json.
- npm install in offline mode failed with ENOTCACHED for Vitest.
- The first frontend build identified TypeScript test-global and React import errors. Those were corrected; subsequent build and Vitest runs passed.
- python --version still cannot launch the Windows Store alias.

## Decisions

- Continue the same project in its current location, C:Usersishav rajDesktopprojectG-one, because the previous gone path no longer exists and this repository contains the Phase 0 commits.
- Preserve the pinned frontend dependencies and lockfile. Exclude generated dependencies from Git.
- Stop before Phase 2 because the Phase 1 backend, database, and browser gates remain unverified.

## Deviations and cut items

- Phase 1 remains incomplete. The backend and authentication source is not runtime-verified. Full role, lockout, session-expiry, CSRF and migration tests remain to be run.
- Browser login and the visual UI review were not run.
- Tailwind tokens and configuration are present; no frontend test suite beyond the current two tests was added.

## Known defects / risks

- Python runtime and PostgreSQL were unavailable, so backend syntax, imports, migration behavior, and auth behavior may still contain defects.
- The browser flow and the new login CSRF challenge have not been exercised end to end.
- Visual review remains UNVERIFIED.

## Next phase prerequisites

- Restore working Python 3.11+ and PostgreSQL, or Docker Desktop daemon access.
- Provide Playwright/Chromium for the required browser and UI gates.
- Re-run all Phase 1 backend, browser, and UI checks before advancing to Phase 2.
