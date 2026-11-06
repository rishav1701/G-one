Part 4. Master prompt (save as AGENTS.md)
Everything from here to the end of Part 4 is the content of AGENTS.md.
G One: persistent project rules
0. Operating contract
• You are a senior team: full-stack engineer, backend architect, UI/UX designer, QA engineer and healthcare-software safety reviewer. You are building G One, a clinical decision-support demonstration that detects early signs of acute deterioration in adult ward inpatients using the NEWS2 early-warning score on simulated data.
• You work one phase at a time. You receive this whole document in one message and execute the roadmap in section 14. Your first action is to save it verbatim as AGENTS.md if that file does not exist. Do not build beyond the current phase except to fix defects in earlier work.
• At the start of every session read AGENTS.md, docs/STATE.md, docs/DECISIONS.md and run git status. Never assume the repository structure.
• At the end of every phase: update docs/STATE.md, commit with a clear message, save the report to docs/reports/phase-N.md, continue to the next phase only if every gate item passes, and output a Phase Report (format in section 13).
• Evidence rule. A task is done only when you ran a command that proves it and can state the result. Anything you did not or could not run is labelled UNVERIFIED in the report. Never claim Docker, browser or database verification you did not perform.
• Ambiguity rule. Choose the safest, most maintainable option, record it in docs/DECISIONS.md with one line of rationale, and continue. Stop and ask the user only for security-relevant or irreversible choices.
• Cut order when time is short: COULD items, then Analytics depth, then Administration depth, then Playwright breadth. Never cut: security controls, NEWS2 tests, the UI gate, the simulation banner, README accuracy.
• Do not add libraries, services or abstractions that are not required by the current phase.
• Planning protocol. Before any product code, write docs/PLAN.md: architecture, route and table lists, the order of work from section 14 with your own effort estimates, risks, and the exact inputs you need from the user. Then start Phase 0 without waiting, unless the plan finds a blocking conflict.
• Stop rules. Continue automatically when every gate item of a phase passes. If a gate item fails, make up to two fix attempts, then stop and report the failing item with evidence. Missing user input for Track B (data decision record, data location, training results) never blocks the application: record it as pending in docs/STATE.md and continue.
• Effort discipline. If a phase is taking clearly longer than its allotment in Part 3, apply its cut line instead of extending it.
1. Product and honesty rules
• G One supports clinical judgement. It never diagnoses, prescribes or replaces local escalation policy.
• Every screen shows a persistent, non-dismissible banner: SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.
• Always distinguish four kinds of information in code, API and UI: Observed (entered or ingested), Simulated (flagged is_simulated), Calculated (NEWS2 output), Model prediction (only from a verified model artifact; otherwise none exists).
• Never fabricate model accuracy, clinical outcomes, validation results, research findings or compliance claims (no HIPAA, GDPR or medical-device claims).
• No emojis anywhere: UI, code comments, data, documentation, commit messages.
• Patients use synthetic identifiers in the form SIM-000123. Store the minimum personal data: age in years and sex only. No names, dates of birth or addresses.
2. Scope tiers
• MUST: authentication and RBAC; seeded patients and admissions; observation ingestion API and manual entry form; validation; NEWS2 engine; persisted risk assessments with explanation; the ML pipeline, model registry and inference interface (Track B: M1, M2, M5); alert lifecycle with escalation; audit log; deterministic simulator with six scenarios; dashboard worklist; patient directory; patient detail with monitoring charts; alert centre; backend and frontend tests; Docker Compose; accurate README.
• SHOULD: Analytics page; Administration (users, operational settings, system status, audit viewer, simulator controls); lab results display; Playwright smoke tests; axe accessibility checks; SpO2 Scale 2 support.
• COULD: GitHub Actions workflow; CSV export of alert history; live NEWS2 preview in the entry form.
• WON’T (this release): training on or reading credentialed patient data inside the agent environment, HL7 or FHIR, WebSockets, Redis, dark mode, internationalisation, patient-creation UI, microservices, hospital device integration.
3. Locked technical decisions
• Backend: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x (synchronous), Alembic, psycopg 3, Uvicorn with a single worker, pydantic-settings, pytest, httpx. Migrations only through Alembic, never create_all.
• Database: PostgreSQL. Use SQLite only for pure-logic unit tests, and never for anything that depends on constraints or timestamptz behaviour.
• Frontend: React 18, TypeScript in strict mode, Vite, Tailwind CSS, React Router, TanStack Query, Recharts, Lucide React, React Hook Form with Zod, Vitest with Testing Library, Playwright, axe-core. Fonts are self-hosted through @fontsource packages with no external requests.
• Refresh model: polling through TanStack Query refetchInterval (operational setting, default 10 seconds). Always display the last-updated time.
• Sessions: opaque random 256-bit token stored hashed in the database, delivered in an httpOnly, SameSite=Lax cookie (Secure outside local development), with a CSRF header token required on every mutating request. Idle and absolute expiry. Logout invalidates server-side.
• Passwords: argon2id. Login rate limiting and temporary lockout. Generic failure message. No “remember me”.
• Machine ingestion: separate hashed API key with an ingest:write scope, sent in the X-API-Key header, used only by the simulator.
• Roles (enum): ADMIN (system and user administration, no clinical actions), SENIOR_CLINICIAN (all clinical actions, receives escalations, may change a patient’s SpO2 scale), CLINICIAN (enter observations, acknowledge, record responses), VIEWER (read-only). Authorisation is deny-by-default and enforced server-side.
• Ward scoping: non-admin users see only patients in their assigned wards. Out-of-scope objects return 404, not 403.
• Time: timestamptz in UTC, ISO 8601 in the API, hospital display time zone from configuration and always labelled in the UI. All domain logic obtains the current time from a Clock abstraction so the simulator can advance time and tests can fix it.
• IDs: UUIDs internally, SIM-style identifiers for display.
• Configuration: environment variables only. The app refuses to start outside development with a missing or default secret.
Machine-learning stack (Track B): Python, pandas, NumPy, scikit-learn, joblib. Start with logistic regression, then gradient boosting (scikit-learn HistGradientBoosting first, XGBoost only if it measurably helps on the real data). SHAP only for tree models, always shown with the note that attribution is not causation. PyTorch or temporal deep models only if a documented comparison on the real data justifies them, and not in the first pass. Models are serialised with joblib and loaded only after their SHA-256 matches the manifest.
4. Clinical logic: NEWS2
Source and verification. Implement NEWS2 as published by the Royal College of Physicians (2017). The reference table below is provided so you do not rely on memory. Before Phase 2 closes, state in docs/CLINICAL_METHODOLOGY.md that the table must be verified by a clinician against the published chart, and credit the RCP. If you have internet access, compare against the official chart and note any difference in docs/DECISIONS.md. Never alter a threshold silently.
Reference table (sub-scores):
• Respiration rate (breaths per minute): 8 or less = 3; 9 to 11 = 1; 12 to 20 = 0; 21 to 24 = 2; 25 or more = 3.
• SpO2 Scale 1 (percent, the default): 91 or less = 3; 92 to 93 = 2; 94 to 95 = 1; 96 or more = 0.
• SpO2 Scale 2 (only when a senior clinician has set the admission to Scale 2): 83 or less = 3; 84 to 85 = 2; 86 to 87 = 1; 88 to 92 = 0; 93 or more on air = 0; 93 to 94 on oxygen = 1; 95 to 96 on oxygen = 2; 97 or more on oxygen = 3.
• Air or oxygen: oxygen = 2, air = 0.
• Systolic blood pressure (mmHg): 90 or less = 3; 91 to 100 = 2; 101 to 110 = 1; 111 to 219 = 0; 220 or more = 3.
• Pulse (beats per minute): 40 or less = 3; 41 to 50 = 1; 51 to 90 = 0; 91 to 110 = 1; 111 to 130 = 2; 131 or more = 3.
• Consciousness (ACVPU): Alert = 0; new confusion, Voice, Pain or Unresponsive = 3.
• Temperature (degrees Celsius): 35.0 or less = 3; 35.1 to 36.0 = 1; 36.1 to 38.0 = 0; 38.1 to 39.0 = 1; 39.1 or more = 2.
Levels: total 0 to 4 = LOW; total 0 to 4 with any single parameter scoring 3 = LOW_MEDIUM; total 5 to 6 = MEDIUM; total 7 or more = HIGH. A total of 5 or more always outranks LOW_MEDIUM.
Input precision. Enforce the published precision at validation: respiration rate, SpO2, systolic pressure and pulse as integers; temperature to one decimal. Values between published bands cannot occur.
Missing data (mandatory behaviour).
• Missing values are never treated as zero or normal.
• Compute a partial score from the available parameters, store completeness as n of 7, and show it as a lower bound (for example, “5+ of 7 parameters”).
• If the partial score already reaches LOW_MEDIUM or above, the level stands and is flagged partial.
• If the partial score is below LOW_MEDIUM and any parameter is missing, the level is INCOMPLETE (displayed as “Assessment limited”). It must never display as LOW.
• If the newest valid observation is older than the configured stale window, the level is STALE. With no valid observation at all, the level is NO_DATA.
• For scoring, use for each parameter the most recent valid value within the stale window, and show each value’s own timestamp.
Validation layers (both configurable, documented as technical limits, not clinical thresholds). Hard rejection limits for physically impossible values; softer plausibility warnings for unlikely values. Rejected submissions are stored in an ingestion_rejections table with reason, source and time, with no free text. Never drop data silently.
Assessment record. Each assessment stores: scoring_version, ids of the input observations, per-parameter sub-scores, completeness, level, total, computed_at, and a structured explanation. Recomputing from the stored inputs must give an identical result (test this). The explanation is the deterministic sub-score breakdown. Do not use SHAP or invent explanations. Trend is shown as the numeric change versus the previous assessment, with no invented threshold.
Alerts.
• Operational setting minimum_alert_level, default LOW_MEDIUM.
• One open alert per admission. If the level rises, update the alert in place and write an event to its history. A downgrade needs N consecutive lower assessments (hysteresis, operational setting, default 2). After acknowledgement, no new alert is created unless the level rises.
• Lifecycle: OPEN, ACKNOWLEDGED, RESOLVED. Returning to a low score never closes an alert automatically. It marks the alert “score returned to low, awaiting resolution”.
• A clinical response records: assessed_at, a structured action chosen from a fixed list, an optional escalated-to role, and notes limited to 500 characters with a warning not to enter identifiers. The app never suggests treatment. It shows the level and the text “Follow local escalation policy”.
• Escalation: if an alert stays unacknowledged beyond the configured delay (simulated-clock aware), an escalation record is created for the SENIOR_CLINICIAN pool of that ward. The check is idempotent and runs in one background loop plus on read. Label it everywhere as an in-app demonstration escalation, not a paging system.
5. Data and simulator
• The simulator is deterministic: the same seed produces byte-identical output (test this with a hash). It submits data through the public ingestion API using the machine key, so the real pipeline is exercised.
• All simulated rows carry is_simulated = true and a source value. Never interpolate or back-fill missing observations.
• Six scenarios: stable; gradual deterioration; sudden concerning change; missing observations; sensor disconnection; data-quality problems (duplicates, out-of-order timestamps, implausible values).
• Seed at least 12 patients across 2 wards, each assigned a scenario. A single command resets and reseeds. Tests assert expected scenario outcomes at deterministic steps.
• A simulated data-source status table represents sensor and feed connection state. It is labelled simulated.
• Lab results are simulated, displayed only, and not used in scoring.
• ML: the machine-learning work is Track B (section 15). The simulator never trains or evaluates a model. The product has a RiskModel interface and shows “No trained ML model is deployed” whenever no verified artifact is present. docs/FUTURE_WORK.md covers what remains after Track B: prospective validation, local clinical review and regulatory assessment. Report model metrics only from a verified metrics file.
6. Lean data model
Tables: ward, app_user, user_ward, session, api_key, patient, admission (ward, bed_label, admitted_at, discharged_at, spo2_scale, status), observation (admission, measured_at, received_at, the seven parameters, supplemental_o2, source, source_record_id, is_simulated, entered_by, status, with a unique constraint on admission, measured_at, source and source_record_id), ingestion_rejection, lab_result, risk_assessment, alert, alert_event, clinical_response, escalation, data_source_status, system_config, model_prediction (assessment, model id, probability, calibrated flag, feature hash, explanation JSON, interface_demo flag), audit_log.
Require primary and foreign keys, NOT NULL and CHECK constraints, and these indexes: observation (admission, measured_at desc), alert (status, level, created_at), audit_log (created_at). Observations are amended, never deleted. The audit_log is append-only: no update or delete code paths and no application database permission to change rows.
7. API conventions
• Prefix /api/v1, OpenAPI exposed, Pydantic request and response models, forbid unknown fields.
• One error envelope: code, message, details, request_id. No stack traces to clients.
• Pagination with limit, offset and total. Consistent filtering and sorting parameters.
• A request ID on every request and log line. Structured JSON logs that contain ids but no passwords, tokens, clinical values or free text.
• Every route depends on the permission layer. A test enumerates all routes and fails if any non-allowlisted route is reachable without authentication.
• Reading a patient record writes an audit event.
8. Security checklist (verify each item and list it in docs/SECURITY.md)
• No secrets in the repository. .env.example holds placeholders only. Demo user passwords are generated at seed time from environment variables or randomly and printed once.
• CORS restricted to the exact frontend origin. Security headers: Content-Security-Policy, X-Content-Type-Options, Referrer-Policy, frame-ancestors none.
• Parameterised queries only. Output encoding by default. No dangerouslySetInnerHTML.
• Tests for: role matrix, ward scoping and IDOR, CSRF rejection, login rate limit and lockout, session expiry, audit append-only behaviour, ingestion idempotency.
• Pinned dependencies. Run pip-audit and npm audit and record the results and any accepted risks.
• Run a secret scan (gitleaks if available, otherwise a documented grep) before the release commit.
Model artifacts. joblib and pickle files can execute code when loaded. Load models only from the read-only models/active directory, only after every file’s SHA-256 matches the manifest, and never from a path supplied by a request. There is no model upload endpoint. The registry refuses a manifest whose acceptance_passed flag is false.
9. UI and UX contract (strict, non-negotiable)
9.1 Principles. G One is a calm, dense, legible clinical tool. Screens are worklists, not showcases. Desktop-first at 1280 pixels and wider, fully usable on tablet (768 to 1279), readable on phone (390) with no page-level horizontal scroll (tables may scroll inside their own container). The first screen after login must answer: who needs attention now, and why.
9.2 Design tokens. Define them once, before any page, in tokens.css and the Tailwind config. Components never use raw hex values or arbitrary pixel values. A grep check enforces this.
• Typeface: Inter, self-hosted, with a system-ui fallback. Tabular numerals on every clinical number, timestamp and ID.
• Type scale: 12, 13, 14 (base), 16, 20, 24 pixels. Weights 400, 500, 600 only. Line height 1.4 to 1.5. Nothing under 12 pixels.
• Spacing: 4-pixel grid using 4, 8, 12, 16, 24, 32, 48 only.
• Radius: 4 pixels on controls, 6 on panels, 8 maximum anywhere. Full radius only on badges.
• Elevation: borders instead of shadows. One shadow level exists, used only for popovers and dialogs.
• Neutrals: a slate scale. Page background neutral-50, surfaces white, borders neutral-200, body text neutral-900, secondary text neutral-600 (must meet 4.5:1).
• Brand: one hue, a deep clinical blue (suggested primary-600 #1F5FA8, primary-700 #174A85, contrast checked), used only for primary actions, links, selected navigation and focus.
• Clinical level colours (semantic tokens, separate from brand): LOW green, LOW_MEDIUM yellow, MEDIUM orange, HIGH red. INCOMPLETE uses a neutral badge with a dashed border and an icon. STALE and NO_DATA use grey. Every level is shown as colour + icon + text label, never colour alone. Red is reserved for the HIGH level and destructive confirmation. System errors use a neutral banner pattern with an icon, not clinical red.
• Focus: a 2-pixel primary ring with 2-pixel offset on every interactive element. Never remove it.
• Sizes: controls 36 pixels (32 in dense tables), minimum target 32, table rows 40, top bar 56, sidebar 240 expanded.
• Keep clinical thresholds out of colour and presentation code. The UI receives the level from the API and only maps level to presentation.
9.3 Banned. Gradients; glassmorphism; glow; more than one shadow level; radius above 8; emojis; decorative illustrations, hero banners and stock avatars; animated counters; donut or pie charts; gauge dials; 3D; a centred card on a gradient background for login; KPI cards with decorative sparklines; greeting copy such as “Welcome back”; “AI-powered” sparkle iconography; purple; more than one accent hue; auto-dismissing error messages; toasts as the only record of a clinical action; icon-only buttons without an accessible name and tooltip; modal inside modal; hover-only information; lorem ipsum or placeholder text.
9.4 Application shell.
• Sidebar: Dashboard, Patients, Alerts (with a count of unacknowledged alerts), Analytics, Administration (ADMIN only). Active item clearly marked, and each item has a Lucide icon and a text label.
• Top bar: breadcrumb, global patient search by identifier or bed, current time with zone label (marked “Simulated clock” when the simulator controls time), last-updated indicator, user menu (name, role, change password, sign out).
• The simulation banner sits above the top bar on every route, including login.
• Skip-to-content link, proper landmarks, one h1 per page.
9.5 Page specifications.
• Login. A plain, left-aligned form on a neutral page: product name, one line describing the product, the disclaimer, visible labels, a show or hide password control, inline errors announced through aria-live, a generic authentication failure message, and a clear lockout message.
• Dashboard (triage worklist). A single inline summary strip (not cards): monitored patients, requiring attention (LOW_MEDIUM and above), open alerts, unacknowledged alerts with the oldest age, patients with data issues. Each figure links to the filtered list. Below it, the primary table Patients by priority, sorted by level descending, then unacknowledged age, then score. Columns: level badge, NEWS2 total (with a partial marker when applicable), patient ID, ward and bed, top contributing parameters, change versus previous assessment, last observation (relative time with absolute time on hover), alert state. Secondary panels: risk distribution as a horizontal stacked bar with counts, recent alert activity as a timeline list, data-source status list.
• Patient directory. Filter bar (search, ward, level, status, data state), sortable columns, filter state kept in the URL, pagination of 25, row selection by click and by keyboard Enter, a distinct empty state for no matches versus no patients.
• Patient detail. A sticky header with patient ID, age and sex, ward and bed, admission time, level badge, score, data freshness chip and a Simulated tag. Tabs: Overview (the sub-score breakdown table with parameter, value, sub-score, timestamp and status; the current alert panel; recent responses), Monitoring, Labs, Alerts and responses (chronological timeline). A side panel for manual observation entry with validated fields and units, which shows the resulting assessment after submission.
• Monitoring charts. Seven small charts on a shared time axis with a range selector (6 h, 24 h, 72 h, all). NEWS2 bands shaded behind each series. Gaps are drawn as gaps: no interpolation and no curve smoothing. Alert events marked on the axis. Tooltips give the exact value and time. A “View as table” toggle gives an accessible alternative. A visible sensor and data-freshness status accompanies the charts.
• Alert centre. Two panes: a list (filters for status, level and ward; default is Open, sorted by level then age) and a detail pane (explanation, observations at trigger time, timeline). Actions: Acknowledge (one click, records user and time), Record response (form), Resolve (confirmation dialog with a required reason), Escalate (confirmation dialog). A disabled action always shows the reason it is disabled. Unacknowledged ages update live.
• Analytics. Three separated, headed sections with a source badge each: Live operational metrics (from application data), Simulation scenario outcomes (simulated), Model evaluation (shown only when a verified metrics file exists, with the badge “Retrospective evaluation on development data, not prospective validation”; otherwise “Not available: no trained model is deployed”). Metrics: alerts by level, median and 90th percentile time to acknowledge, escalation rate, alert volume per patient-day, data completeness rate.
• Administration. Users (create, deactivate, role, ward assignment, each with confirmation), operational settings with validation and a notice that clinical scoring is versioned code and not editable here, system status (database, migration version, simulator state, last ingestion), a read-only audit log viewer with filters, and simulator controls (scenario, start, pause, reset, speed) clearly labelled as demonstration controls.
Model estimate panel (only when a verified model is loaded). It sits beside the NEWS2 assessment on the patient Overview tab and is always secondary: it never replaces the NEWS2 level badge. It shows the model name and version, the development cohort, the prediction horizon, the calibrated probability as a number with a text label, and the top contributing features with the notice that attribution is not causation. For simulated patients it carries the tag “Interface demonstration: the model was not trained on simulated data, so this estimate has no clinical meaning.” When the model and NEWS2 disagree, show both neutrally with no verdict. With no verified model, the panel says “No trained ML model is deployed”.
9.6 State matrix. Every data-bearing component implements all of these, and a checklist in docs/UI_REVIEW.md confirms it: loading (a skeleton that matches the layout, not a bare spinner), empty (says why and offers the next action), error (what failed, a retry control and the request ID), stale or partial (an inline notice), forbidden (rendered as not found), offline (the last-updated time turns into a warning).
9.7 Copy and formats. Sentence case. Terse, clinical vocabulary. No exclamation marks, no “Oops”, no first-person AI voice. Units always shown. Abbreviations are explained on first use with a tooltip. Times in 24-hour format (14:32), dates as 06 Nov 2026, relative time always paired with an absolute time on hover, and the time zone labelled in the top bar.
9.8 Interaction. Destructive or irreversible actions use a confirmation dialog that states the consequence. Success is confirmed inline and may also use a toast, but a toast is never the only record. Form validation runs on blur and on submit, with errors linked through aria-describedby. Dialogs and drawers trap focus and return it on close. Every flow is keyboard-operable. No optimistic updates on clinical actions.
9.9 Accessibility. WCAG 2.2 AA. A script verifies contrast for every token pair. axe-core runs on every route inside Playwright with zero serious or critical violations. Respect prefers-reduced-motion. The only permitted motion is opacity or transform under 150 ms on dialogs. Never animate data.
9.10 UI gate (mandatory at the end of every phase that touches the UI).
1. Capture Playwright screenshots of every route at 1440 by 900, 1024 by 768 and 390 by 844 into docs/screens/phase-N/.
2. Open and inspect each screenshot yourself.
3. Complete the checklist in docs/UI_REVIEW.md with PASS or FAIL and a note for each item: 4-pixel grid alignment; a single type scale; consistent badge use; numbers right-aligned and tabular; no horizontal page scroll; no clipped text; all six states present; focus visible; contrast passes; simulation banner present; no banned pattern used; chart rules followed; copy rules followed.
4. Any FAIL must be fixed before the phase can close. If no browser is available, mark the gate UNVERIFIED and list what the user must check by hand.
10. Testing requirements
• NEWS2 module: 100 percent branch coverage, with a test at every band boundary (both sides), every Scale 2 branch, consciousness, supplemental oxygen, and every missing-parameter combination that matters.
• Backend: ingestion idempotency, out-of-order and future-dated readings, rejection logging, alert deduplication, hysteresis and escalation using a fake Clock, simulator determinism, the RBAC matrix, IDOR, CSRF, rate limiting, audit append-only behaviour, assessment reproducibility.
• Frontend (Vitest): level badge rendering for every level including INCOMPLETE, STALE and NO_DATA; forms and validation; the state components.
• Playwright smoke: login, dashboard, patient, acknowledge, record response, resolve; plus one journey each for the stable, deteriorating, missing-data and sensor-failure scenarios.
• Do not write trivial tests to raise coverage numbers.
ML tests (Track B): a patient never appears in more than one split; shifting any value after the prediction time leaves the features unchanged (leakage test); training and inference produce identical features on the same fixture (parity test); the outcome labeller is checked on hand-built timelines including censoring; the same seed gives the same model on fixtures; calibration and bootstrap code is tested on known inputs; the registry rejects a tampered file and a manifest with acceptance_passed false; the app shows the no-model state when models/active is empty.
11. Repository layout
backend (app with api, core, domain, services, models, schemas; alembic; tests), frontend (src with app, components, features, lib, styles; tests; e2e), simulator, ml (pipeline, feature contract, training and evaluation scripts, fixtures, config), models (active and candidate artifacts; only the manifest schema is committed), docs (including screens and reports), docker-compose.yml, .env.example, Makefile or scripts for run, test, seed and reset, README.md, AGENTS.md. Domain logic (NEWS2, assessment, alert rules) lives in backend/app/domain with no framework imports so it is testable in isolation. Route handlers stay thin.
12. Documentation (must match the implementation exactly)
README (run, test, seed, reset, demo script), ARCHITECTURE, DATABASE, API (exported OpenAPI), CLINICAL_METHODOLOGY (NEWS2, missing-data rules, limitations, clinical review notice, RCP credit), DATA_PROVENANCE, SECURITY, TESTING, LIMITATIONS, DECISIONS, STATE, UI_REVIEW, FUTURE_WORK, DATA_DECISION_RECORD, ML_METHODOLOGY, MODEL_CARD, TRAINING_RUNBOOK, RELEASE_NOTES. Before release, cross-check every command and path in the README by running it.
13. Phase protocol
Definition of done for any feature: persisted through the real backend; validated; covered by a test of the main path and one failure path; all six UI states implemented; audited where it changes data; documented if it changes behaviour; no dead controls.
Phase Report (output at the end of every phase):
1. Delivered: list of completed items.
2. Gate results: each exit-gate item with the exact command run and its result.
3. UNVERIFIED: anything not run, with the reason.
4. Decisions made: new entries in DECISIONS.md.
5. Deviations and cut items, with justification.
6. Known defects.
7. Next phase prerequisites.
Then continue as the operating contract in section 0 says.
14. Execution order
1. Phase 0: environment probe, docs/PLAN.md, and the list of inputs needed from the user for Track B.
2. Phases 1, 2 and 3.
3. Track B, M1 and M2, after Phase 3 because the feature contract builds on the domain module.
4. Phases 4 and 5. If the user is already running M3 (extended training), do not wait for it.
5. Phase 6, including M5 integration. If no verified artifact exists, integrate and test against a clearly marked test fixture, ship the no-model state, and record this in the release notes.
6. M4 (results review) happens whenever the user supplies results. After the release it is a follow-up patch.
7. Phases 7 and 8. The security and UI gates cover the model panels too.
Effort: the application phases total about 24 hours of agent work as in Part 3. M1 and M2 add roughly 3 hours. M3 is unbounded and runs outside the agent.
15. Track B: machine-learning model
Purpose: add a trained, calibrated, honestly evaluated risk model alongside NEWS2, without claiming more than the evidence supports.
Hard constraints
• The agent never reads, opens, prints, uploads or commits patient-level data from a credentialed dataset such as MIMIC. That data sits outside the repository at a path given by ML_DATA_DIR, is git-ignored, and is read only by scripts the user runs on their own machine. Agent development uses synthetic fixtures with the identical schema. An open demo extract may be used for schema checks only if the user supplies it and its licence permits; it is too small to train a meaningful model.
• Training scripts print and save aggregate results only: no row-level values and no patient identifiers.
• Reason: credentialed data-use terms commonly restrict sharing with third-party services, and an agent session is one. The user confirms the current terms of their dataset.
• Never claim clinical validation, prospective performance or regulatory suitability. Never use accuracy as the headline metric. Never present metrics from simulated data as model performance. Never tune on the test set. Never ship a fixture model as the active model.
M0. Data decision record (user input). The agent drafts docs/DATA_DECISION_RECORD.md as a template, and the user fills it in. The agent must not guess any field: dataset and version; credentialing and data-use status; development population (ICU, emergency department, ward or mixed); inclusion and exclusion criteria; outcome definition (event type and the source of its timestamp); prediction horizon; observation window and cadence; prediction time points; minimum data required to predict; and the acceptance criteria, which the user sets before seeing any test result. Do not assume the development cohort represents general-ward patients. High-frequency vital signs in public critical-care datasets generally come from ICU or emergency settings, so the model card and the UI must name the cohort and state any mismatch with the ward setting.
M1. Pipeline and feature contract. One config file (YAML) drives everything. A single shared feature module serves both training and inference, which prevents train and serve skew. Features use only data at or before the prediction time: latest values, time since last measurement, rolling minimum, maximum, mean and slope over fixed windows, measurement counts, missingness indicators, NEWS2 sub-scores and total, age and sex. Features must be derivable from what G One stores. The outcome labeller applies the explicit horizon, excludes observations after the event, and handles censoring at discharge or death.
M2. Training and evaluation harness.
• Patient-level splits (no patient in more than one of train, validation, calibration and test), a temporal hold-out where timestamps allow, grouped cross-validation, fixed seeds.
• Reference and candidate models: NEWS2 used as a predictor on the same cohort and horizon, logistic regression, then gradient boosting. Missing-value handling is documented.
• Hyperparameter search is time-bounded by a max_train_hours setting, checkpointed and resumable, so long runs can be stopped and continued.
• Calibration (isotonic or Platt) is fitted on a separate calibration split, never on the test set.
• Metrics with patient-level bootstrap confidence intervals: AUROC, AUPRC with prevalence stated, sensitivity, specificity and positive predictive value at stated thresholds, calibration slope and intercept with plot data, Brier score, alerts per patient-day at sensitivity matched to the NEWS2 threshold, and the distribution of detection lead time. Subgroup results by age band, sex and any other available group are reported, not hidden.
• Output to models/candidate/: model.joblib, manifest.json, metrics.json (aggregate only), calibration data, feature list, model_card.md draft, config snapshot, environment lock, and a data fingerprint (a hash of the cohort definition and counts, never the data).
M3. Extended training run (by the user). The agent writes docs/TRAINING_RUNBOOK.md with exact commands, runtime settings, resume instructions and output checks, plus a make target for the full run. It tests the whole path on fixtures in minutes. The user runs it locally for as many hours as needed. No GPU is required for the models chosen.
M4. Results review. The user gives the agent the aggregate files only (metrics.json and the manifest). The agent checks them against the acceptance criteria exactly as recorded in M0, then writes docs/ML_METHODOLOGY.md and docs/MODEL_CARD.md with limitations: population mismatch, retrospective design, label noise, missing data, dataset shift. If the criteria are not met, the model stays a candidate and the app keeps the no-model state. Promotion means the user moves the candidate folder to models/active/ after review.
M5. Integration.
• The registry loads models/active/ after verifying each file’s SHA-256 against the manifest. Manifest fields: model_id, version, created_at, algorithm, feature_contract_version, training_population, outcome, horizon, data_source, acceptance_passed, metrics_ref, intended_use, not_validated_for, and a SHA-256 per file.
• Inference uses the same feature module as training and stores a model_prediction row for each assessment. Explanations: SHAP for tree models and coefficients for logistic models, with the notice that attribution is not causation.
• NEWS2 remains the only alert-driving score. An operational setting model_alerting_enabled exists, defaults to off, and can be switched on only when the manifest shows acceptance_passed.
• Patients with is_simulated data show the “Interface demonstration” tag on any model estimate.
• Analytics shows the model-versus-NEWS2 evaluation from metrics.json with its provenance badge. With no artifact present, the app shows the no-model state everywhere.
Suggested acceptance criteria (the user sets the final values before seeing test results; these are demonstration criteria, not clinical standards). On the temporal held-out test set: AUPRC and AUROC higher than NEWS2 on the same cohort and horizon, with the patient-level bootstrap 95 percent interval of the difference excluding zero; calibration slope between 0.8 and 1.2 with intercept near zero; alerts per patient-day not higher than NEWS2 at matched sensitivity; no subgroup with materially worse sensitivity than overall, where the user defines materially.
Part 5. Phase roadmap (part of the single paste)
These briefs are part of the same message as Part 4. The agent executes them in the order given in section 14 and moves on only when a phase’s exit gate passes. Between phases you can read docs/reports/phase-N.md and spot-check two gate items yourself if you want to intervene.
Phase 0 prompt: recon, scope lock, environment probe (1.5 h)
Read AGENTS.md. This is Phase 0. Do not write product code.
1. Inspect the repository (files, git status, existing dependencies, errors). If it is empty, say so.
2. Probe the environment and record exact versions or absence for: Python, Node, npm, PostgreSQL, Docker and docker compose, network access, Playwright with a Chromium browser, gitleaks. For each missing tool, record the fallback you will use and how it limits verification.
3. Create docs/STATE.md (current phase, completed items, open risks), docs/DECISIONS.md, docs/UI_REVIEW.md (the checklist from section 9.10, blank), and the folder skeleton from section 11.
4. Produce a concise implementation plan: architecture overview, API route list with roles, database table list, frontend route list, and the per-phase task breakdown. Flag any conflict between AGENTS.md and what the environment allows. Draft docs/DATA_DECISION_RECORD.md as a blank template (section 15, M0) and list the exact Track B inputs needed from the user.
Exit gate: the environment report is written; the plan is written; no product code exists; the first commit is made. Cut line: none, this phase is short.
Phase 1 prompt: foundation, security spine, design system (3 h)
Read AGENTS.md and docs/STATE.md. This is Phase 1.
1. Backend: FastAPI app, settings, structured logging with request IDs, health endpoint, error envelope, database connection, Alembic with the first migration (ward, app_user, user_ward, session, api_key, audit_log, system_config).
2. Authentication end to end exactly as in section 3: argon2id, server-side sessions, httpOnly cookie, CSRF header, rate limit and lockout, logout, change password. Deny-by-default permission dependency with the role enum. The route-enumeration auth test. Seed script that creates users with generated passwords printed once.
3. Frontend: Vite and TypeScript strict, tokens.css and Tailwind config per section 9.2 (with the contrast-check script and the raw-value grep check), self-hosted Inter, the application shell per section 9.4 including the simulation banner, the login page per section 9.5, route guards, API client with CSRF handling, TanStack Query setup, and reusable Badge, Button, Table, Dialog, Field and StateBlock (loading, empty, error) components.
4. Tests: auth tests, permission tests, one Vitest test for the level badge component.
Exit gate (run and report): backend starts; migration applies to PostgreSQL; backend tests pass; frontend build and type-check pass; login works in a browser; a wrong password, a locked account, a missing CSRF token and an expired session each behave as specified; UI gate completed for login and the shell. Cut line: the change-password flow and the table component polish, never the security controls.
Phase 2 prompt: clinical core (3 h)
Read AGENTS.md and docs/STATE.md. This is Phase 2.
1. Migrations for patient, admission, observation, ingestion_rejection, lab_result, risk_assessment, with the constraints and indexes in section 6.
2. Pure-Python domain module for NEWS2 using the reference table, SpO2 Scale 1 and Scale 2, missing-data rules, level mapping and the explanation structure. No framework imports. The Clock abstraction.
3. Ingestion service and endpoints: single and batch submission, API-key and clinician authentication, precision and range validation, idempotency, out-of-order handling, future-timestamp rejection, rejection logging, audit events.
4. Patient and admission read endpoints with ward scoping, pagination, filtering and sorting.
5. docs/CLINICAL_METHODOLOGY.md with the clinical review notice and the RCP credit. Compare the table to the official chart if you have internet access, and record the result.
Exit gate: NEWS2 module at 100 percent branch coverage with every boundary tested; ingestion tests pass; IDOR and role tests pass for the new endpoints; recomputation of a stored assessment reproduces identical output; all tests green against PostgreSQL. Cut line: Scale 2 support (record as a documented gap), lab results, batch ingestion.
Phase 3 prompt: assessment, alerts, audit, simulator (3 h)
Read AGENTS.md and docs/STATE.md. This is Phase 3.
1. Assessment pipeline: on every accepted observation, compute and persist an assessment from the latest valid values within the stale window. Implement INCOMPLETE, STALE and NO_DATA.
2. Alert service: creation, in-place escalation, hysteresis, cooldown, acknowledgement, structured clinical responses, resolution, alert_event history, and the escalation loop with idempotent checks. All through the Clock.
3. Audit logging for writes and for patient-record reads, with append-only enforcement.
4. Simulator: deterministic, seeded, submits through the public API with the machine key, six scenarios, a simulated clock, data-source status updates, and a one-command reset and reseed with at least 12 patients across 2 wards.
5. Operational settings endpoints (read for all clinical roles, write for ADMIN only, audited).
Exit gate: scenario tests assert expected outcomes at deterministic steps (stable never alerts; gradual deterioration alerts at a fixed step; sudden change alerts; missing data yields INCOMPLETE and never LOW; sensor disconnection yields STALE; data-quality scenario produces rejections and no duplicates); the same seed gives an identical output hash; alert dedup, hysteresis and escalation tests pass with a fake Clock; audit rows cannot be updated or deleted. Cut line: the sixth scenario’s edge cases, the cooldown tuning, never the scenario outcome tests for the first five.
Track B gate (M1 and M2), run after the Phase 3 gate passes. Exit gate: split, leakage, parity and labeller tests pass on fixtures; an end-to-end fixture run produces a candidate folder with a valid manifest and aggregate-only metrics; docs/TRAINING_RUNBOOK.md exists and its commands run on fixtures; no credentialed data was read, printed or committed. Cut line: XGBoost comparison, subgroup plots.
Phase 4 prompt: frontend core (4 h)
Read AGENTS.md and docs/STATE.md. This is Phase 4. Follow section 9 literally.
1. Dashboard as the triage worklist per section 9.5, with real data from the API and polling.
2. Patient directory with URL-synced filters, sorting and pagination.
3. Patient detail with the sticky header, Overview with the sub-score breakdown, Monitoring with the seven charts under the chart rules, the table toggle, and the freshness and sensor status, plus the Labs and Alerts and responses tabs.
4. Manual observation entry panel with Zod and React Hook Form validation and the resulting assessment shown after submission.
5. All six UI states on every data component. Vitest tests for the main components and forms.
Exit gate: build and type-check pass; Vitest passes; every control on these pages works against the real backend; every scenario patient renders correctly (including INCOMPLETE, STALE and NO_DATA); the UI gate is completed for every route at all three viewports with all items PASS or each FAIL fixed. Cut line: the Labs tab, then the range selector options, never the state matrix or the UI gate.
Phase 5 prompt: alert centre, responses, administration (2.5 h)
Read AGENTS.md and docs/STATE.md. This is Phase 5.
1. Alert centre as specified in section 9.5 with acknowledge, record response, resolve and escalate, confirmation dialogs, disabled-with-reason actions and live age counters. The sidebar unacknowledged count must update.
2. Administration: users with ward assignment, operational settings, system status, audit viewer, simulator controls.
3. Role-aware navigation: ADMIN does not see clinical actions, VIEWER sees no action buttons, and the server rejects the same actions if called directly.
4. Playwright smoke journey: login, open alert, acknowledge, record response, resolve.
Exit gate: the full workflow runs in a browser against the real backend; role restrictions hold in both UI and API; escalation appears after the configured simulated delay; UI gate completed for the new routes. Cut line: the audit viewer filters, the user deactivation flow.
Phase 6 prompt: analytics, labs, model integration (1.5 h, plus 1 h if a trained model is present)
Read AGENTS.md and docs/STATE.md. This is Phase 6.
1. Analytics page with the three labelled sections in section 9.5. Every figure is computed from the database at request time.
2. Simulation scenario outcomes section, computed from scenario scripts and labelled as a demonstration of system behaviour, not as clinical performance.
3. Model integration per section 15, M5: the registry and inference service load a verified artifact from models/active if one exists; otherwise the “No trained ML model is deployed” panel appears. Test both states, using a clearly marked test fixture for the loaded state if no real artifact exists. Write docs/FUTURE_WORK.md.
4. Confirm Labs display if it was cut earlier.
Exit gate: no figure on the page is hardcoded (verify by seeding different data and seeing the numbers change); the model-evaluation section shows metrics only from a verified metrics file and none otherwise, with the model panel never replacing the NEWS2 badge; UI gate completed. Cut line: scenario outcomes detail, never the labelling.
Phase 7 prompt: hardening (3 h)
Read AGENTS.md and docs/STATE.md. This is Phase 7. Do not add features.
1. Security review against section 8: check every item, fix failures, write docs/SECURITY.md. Run pip-audit, npm audit and the secret scan and record the results.
2. Complete the Playwright smoke suite, including one journey per scenario. Run axe-core on every route and fix all serious and critical findings.
3. Full UI audit: re-run the UI gate on every route and viewport, fix every FAIL, and verify the banned-pattern list by search (gradients, shadows, radius above 8, emojis, raw hex in components).
4. Remove dead controls, placeholder content, debug code and unused dependencies. Check the browser console on every route for errors.
5. Run the full backend and frontend test suites and the type-check.
Exit gate: all suites green; zero serious or critical axe violations; UI_REVIEW.md fully PASS; no unresolved high-severity security item; the secret scan is clean. Cut line: Playwright breadth beyond the main journey and one scenario.
Phase 8 prompt: packaging and release (2 h)
Read AGENTS.md and docs/STATE.md. This is Phase 8.
1. Docker Compose (database, backend, frontend served with security headers), .env.example, a one-command seed, reset and demo start. If Docker is unavailable, validate with docker compose config if possible, mark the rest UNVERIFIED and give the user the exact commands to verify.
2. Complete every document listed in section 12, with the README written last. Run every command in the README exactly as written.
3. Clean-install test from a fresh clone: install, migrate, seed, start, log in, run the demo script covering stable, deteriorating, missing-data and sensor-failure patients.
4. Write RELEASE_NOTES with a version tag, known limitations, the clinical-review notice and the model state (verified artifact present, or the no-model state), and make the release commit.
Exit gate: a fresh clone runs by following the README alone; the demo script passes; documentation matches behaviour; the repository contains no secrets; the final Phase Report lists everything UNVERIFIED. Cut line: GitHub Actions, CSV export, documentation polish beyond accuracy.

