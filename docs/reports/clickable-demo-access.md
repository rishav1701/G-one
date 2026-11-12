# Clickable demo access report — 2026-11-13

This report captures the prior clickable-session implementation before the follow-up that loads credentials into the login form. The latest behavior and checks are recorded in `docs/reports/demo-credential-autofill.md`.

## Delivered at the time

- Made the Demo clinician and Administrator tiles clickable.
- In localhost development, either tile requested a normal audited server-side session for its selected seeded account. The API accepted only `clinician` or `admin` and retained environment, host, CSRF, and rate-limit checks.
- When the local shortcut was disabled, a tile selected the sign-in context, filled the configured username, and focused the password field.

## Gate results at the time

- Frontend tests (22), production build, raw style scan, and contrast check passed.
- Focused backend security checks passed, excluding a database-backed route test because PostgreSQL was unavailable.
- OpenAPI regeneration and JSON parsing passed.

## UNVERIFIED at the time

- Browser screenshot review at desktop, tablet, and mobile sizes, plus axe checks.
- PostgreSQL-backed demo sessions.
