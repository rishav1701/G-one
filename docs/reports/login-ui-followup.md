# Login UI follow-up report — 2026-11-13

## Delivered

- Reworked the G One login into a centered, responsive identity and sign-in panel inspired by the supplied layout, using the existing light clinical blue and neutral palette.
- Added clinical and administration context buttons. The selected context changes the submit label only; the authenticated account continues to determine server-side permissions.
- Added username and password field icons, a prominent sign-in action, local demo clinician access, and administrator account setup guidance.
- Kept the persistent simulation disclaimer, password visibility toggle, generic login errors, and local-only demo session flow. No demo password is displayed or autofilled.

## Gate results

- `npm run test -- --run src/app/Login.test.tsx` (from `frontend/`) — passed, 2 tests.
- `npm run build` (from `frontend/`) — passed, including TypeScript build and Vite production bundle.
- `npm run check:raw` (from `frontend/`) — passed.
- `npm run check:contrast` (from `frontend/`) — passed; all existing measured token pairs remain above 4.5:1.
- `git status --short --branch` — repository was clean before this follow-up.

## UNVERIFIED

- Login screenshots at 1440×900, 1024×768, and 390×844 and manual visual inspection. The in-app browser timed out while opening local Vite; desktop browser control could not safely identify the current URL.
- Playwright and axe checks, and live PostgreSQL/API demo flow. These require the local demo stack and browser inspection to be available.

## Decisions

- The context selector is presentation-only. The server continues to enforce permissions from the signed-in account.
- Quick demo access keeps using the local-only one-click endpoint. The page shows the seeded username and does not reveal the generated password.

## Deviations and known defects

- The required screenshot review remains pending because browser access to the local page was unavailable in this session. No other known defect from this patch.

## Next verification

- Run the local demo, inspect the login at desktop, tablet, and mobile sizes, verify keyboard focus and overflow, and run the browser accessibility checks.
