# UI Review — Phase 1

Reviewed manually from Playwright screenshots at 1440×900, 1024×768, and 390×844. Browser assertions also verified no page-level horizontal scrolling. PASS means the criterion was checked on the named route and viewport.

| Route | Viewport | 4px grid | Type scale | Badge use | Clinical numbers | No horizontal scroll | No clipped text | Six states | Visible focus | Contrast | Banner | No banned patterns | Chart rules | Copy | Evidence |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Login | 1440×900 | PASS | PASS | PASS, none used | PASS, none shown | PASS | PASS | PASS, shared StateBlock supports all six | PASS | PASS | PASS | PASS | PASS, no charts | PASS | docs/screens/phase-1/login-1440.png |
| Login | 1024×768 | PASS | PASS | PASS, none used | PASS, none shown | PASS | PASS | PASS, shared StateBlock supports all six | PASS | PASS | PASS | PASS | PASS, no charts | PASS | docs/screens/phase-1/login-1024.png |
| Login | 390×844 | PASS | PASS | PASS, none used | PASS, none shown | PASS | PASS | PASS, shared StateBlock supports all six | PASS | PASS | PASS | PASS | PASS, no charts | PASS | docs/screens/phase-1/login-390.png |
| Dashboard shell | 1440×900 | PASS | PASS | PASS, none used | PASS, none shown | PASS | PASS | PASS, empty state and shared six-state component | PASS | PASS | PASS | PASS | PASS, no charts | PASS | docs/screens/phase-1/shell-1440.png |
| Dashboard shell | 1024×768 | PASS | PASS | PASS, none used | PASS, none shown | PASS | PASS | PASS, empty state and shared six-state component | PASS | PASS | PASS | PASS | PASS, no charts | PASS | docs/screens/phase-1/shell-1024.png |
| Dashboard shell | 390×844 | PASS | PASS | PASS, none used | PASS, none shown | PASS | PASS | PASS, empty state and shared six-state component | PASS | PASS | PASS | PASS | PASS, no charts | PASS | docs/screens/phase-1/shell-390.png |

Contrast results from the contrast script: body 17.06:1; secondary 7.24:1; primary 6.44:1; banner 17.85:1; LOW 6.81:1; LOW_MEDIUM 6.62:1; MEDIUM 6.88:1; HIGH 5.91:1. Every measured pair exceeds 4.5:1.

# UI Review — Phase 6

Analytics and patient detail additions were reviewed at 1440×900, 1024×768, and 390×844. The Playwright run generated nine screenshots and checked axe-core on each route and viewport; zero serious or critical violations remain. Browser assertions checked the persistent simulation banner, route rendering, page-level overflow, and console errors. Scenario tables remain internally scrollable on narrow screens.

| Route | 1440×900 | 1024×768 | 390×844 | Evidence |
|---|---|---|---|---|
| Analytics | PASS | PASS | PASS | `docs/screens/phase-6/analytics-*.png` |
| Patient overview — no deployed model | PASS | PASS | PASS | `docs/screens/phase-6/patient-model-none-*.png` |
| Patient labs | PASS | PASS | PASS | `docs/screens/phase-6/patient-labs-*.png` |

Analytics displays database-derived operational metrics, the six seeded scenario outcomes labelled as demonstration behaviour, and model evaluation only when verified metrics exist. Patient overview states that no trained model is deployed; the NEWS2 badge remains visible. Lab rows are identified as simulated. Raw style-value checks passed. Contrast pairs: body 17.06:1, secondary 7.24:1, primary 6.44:1, banner 17.85:1, LOW 6.81:1, LOW_MEDIUM 6.62:1, MEDIUM 6.88:1, HIGH 5.91:1.

# UI Review — Phase 7

The full browser suite was rerun after dependency hardening. Every route and viewport row in Phases 1, 4, 5, and 6 passed, and the suite completed without browser console errors. The table below records the route inventory; Phase 4, 5, and 6 Playwright tests run axe-core at all three viewports (51 scans total), check page-level width, and retain screenshots in the phase evidence folders.

| Route | 1440×900 | 1024×768 | 390×844 | Evidence |
|---|---|---|---|---|
| Login and application shell | PASS | PASS | PASS | `docs/screens/phase-1/` |
| Dashboard | PASS | PASS | PASS | `docs/screens/phase-4/dashboard-*.png` |
| Patient directory | PASS | PASS | PASS | `docs/screens/phase-4/patients-*.png` |
| Patient overview and scenario states | PASS | PASS | PASS | `docs/screens/phase-4/patient-overview-*.png` |
| Patient monitoring | PASS | PASS | PASS | `docs/screens/phase-4/patient-monitoring-*.png` |
| Patient labs | PASS | PASS | PASS | `docs/screens/phase-6/patient-labs-*.png` |
| Patient alerts and responses | PASS | PASS | PASS | `docs/screens/phase-4/patient-timeline-*.png` |
| Alert centre | PASS | PASS | PASS | `docs/screens/phase-5/alerts-*.png` |
| Administration — users, settings, status, audit, simulator | PASS | PASS | PASS | `docs/screens/phase-5/admin-*-*.png` |
| Analytics | PASS | PASS | PASS | `docs/screens/phase-6/analytics-*.png` |

The seeded browser journeys cover stable, gradual deterioration, sudden concerning change, missing observations, sensor disconnection, and data quality. Raw-value and contrast scripts passed. Pattern review found no gradients, emojis, raw hex outside token definitions, or radii above 8px except the full-radius status badge. One shadow level remains on the dialog, as permitted by the design contract. The dialog uses borders elsewhere.

The mobile shell initially overflowed at 390 px. The top bar was changed to a three-row grid, and the rerun passed both the browser scroll-width assertion and manual visual review.

# UI Review — Phase 4

Reviewed every named route at 1440×900, 1024×768, and 390×844 using Playwright screenshots. Browser assertions passed for the persistent banner, route render, page-level overflow, console errors, role-restricted observation entry, and the offline notice. Table overflow is contained within its table scroll region. PASS reflects screenshot review and automated checks; the Labs tab honestly reports unavailable demo data.

| Route | 1440×900 | 1024×768 | 390×844 | Evidence |
|---|---|---|---|---|
| Login | PASS | PASS | PASS | `docs/screens/phase-4/login-*.png` |
| Dashboard | PASS | PASS | PASS | `docs/screens/phase-4/dashboard-*.png` |
| Patients | PASS | PASS | PASS | `docs/screens/phase-4/patients-*.png` |
| Patient overview | PASS | PASS | PASS | `docs/screens/phase-4/patient-overview-*.png` |
| Patient monitoring | PASS | PASS | PASS | `docs/screens/phase-4/patient-monitoring-*.png` |
| Patient labs | PASS | PASS | PASS | `docs/screens/phase-4/patient-labs-*.png` |
| Patient alerts and responses | PASS | PASS | PASS | `docs/screens/phase-4/patient-timeline-*.png` |
| Alert centre | PASS | PASS | PASS | `docs/screens/phase-4/alerts-*.png` |

The 24 screenshots above were generated by the passing Playwright run. Page-level horizontal scroll was absent at all three viewports; tables that exceed narrow screens scroll inside their own containers. INCOMPLETE and STALE simulator patients were opened and checked in the browser. NO_DATA presentation is covered by the shared state matrix and badge component tests; the six standard simulator scenarios do not seed a no-observation patient. The overview explicitly renders a NO_DATA badge and no-data state when the API has no assessment.

The raw-value scan passed after replacing a remaining 4px radius with the 4px spacing token. Contrast script results: body 17.06:1, secondary 7.24:1, primary 6.44:1, banner 17.85:1, LOW 6.81:1, LOW_MEDIUM 6.62:1, MEDIUM 6.88:1, HIGH 5.91:1. All tested pairs exceed 4.5:1. Chart series use NEWS2 parameter subscores, score bands, labels, and gap-aware segments; no page-level chart overflow was observed.

# UI Review — Phase 5

All new administration and alert routes were reviewed at 1440×900, 1024×768, and 390×844. The Playwright run captures 18 screenshots and executes axe-core on each captured route and viewport. Zero serious or critical violations remain. Scrollable table regions and the observation-entry region are keyboard-focusable and have accessible names. Browser assertions confirmed page-level fit and the persistent simulation banner.

| Route | 1440×900 | 1024×768 | 390×844 | Evidence |
|---|---|---|---|---|
| Administration — users | PASS | PASS | PASS | `docs/screens/phase-5/admin-users-*.png` |
| Administration — settings | PASS | PASS | PASS | `docs/screens/phase-5/admin-settings-*.png` |
| Administration — status | PASS | PASS | PASS | `docs/screens/phase-5/admin-status-*.png` |
| Administration — audit | PASS | PASS | PASS | `docs/screens/phase-5/admin-audit-*.png` |
| Administration — simulator | PASS | PASS | PASS | `docs/screens/phase-5/admin-simulator-*.png` |
| Alert centre | PASS | PASS | PASS | `docs/screens/phase-5/alerts-*.png` |

The workflow verified user creation and ward assignment, simulated-clock reset and advance, escalation after the configured simulated delay, acknowledge, response recording, and resolution. ADMIN has no clinical action controls; VIEWER has no action controls and cannot access Administration; the backend RBAC tests reject unauthorized operations. Screenshots were visually checked at desktop, tablet, and mobile sizes. The alert table scrolls within its labelled, keyboard-accessible region on narrow screens.

Raw style values and contrast were rerun: both passed. Contrast pairs: body 17.06:1, secondary 7.24:1, primary 6.44:1, banner 17.85:1, LOW 6.81:1, LOW_MEDIUM 6.62:1, MEDIUM 6.88:1, HIGH 5.91:1.

# UI Review — Post-release demo usability follow-up

Status: **UNVERIFIED**. The login page now provides a local-only one-click demo sign-in and explains its role; the Analytics no-model state distinguishes the inactive ICU candidate from a deployed ward model. Frontend tests and the production build pass. A fresh screenshot review and Playwright/axe run could not be completed because the local PostgreSQL/API service was unavailable to this session.

On a working demo host, capture and inspect every route at 1440×900, 1024×768, and 390×844 under `docs/screens/post-release-demo/`. Check the full Phase UI checklist at each required route: 4-pixel grid, type scale, badge use, tabular/right-aligned clinical numbers, no page-level horizontal scroll, no clipped text, six states, visible focus, contrast, simulation banner, banned patterns, chart rules, and copy rules. Specifically verify that the login panel/button is readable at all three sizes, the Analytics research-model note does not imply ward applicability, one-click access is absent outside localhost/development, and the seeded SENIOR_CLINICIAN can save a manual observation while ADMIN remains unable to do so.

# UI Review — Login visual refresh (2026-11-13)

Status: **UNVERIFIED** for screenshot review. The page now has a centered G One identity, clinical/administration sign-in context selector, credential form, local demo clinician tile, and administrator account guidance. It keeps the persistent simulation disclaimer and existing light clinical-blue/neutral tokens; no passwords are shown or autofilled. The context selector does not grant permissions. Focused login tests, production build, raw style value scan, and contrast script passed. An in-app browser connection to the local Vite server timed out; desktop browser inspection was unavailable because the current URL could not be identified. Capture 1440×900, 1024×768, and 390×844 screenshots and inspect wrapping, keyboard focus, and page overflow when a browser is available.

# UI Review — Clickable demo access (2026-11-13)

The two quick-access account tiles are full keyboard-operable buttons. Selecting one synchronously fills its fixed demo username and password into the login fields with no API request; the password remains masked. The normal database-backed login still validates the credentials. Frontend visual browser review is **UNVERIFIED**; capture desktop, tablet, and mobile screenshots and run axe when browser access is available.
