# Environment probe — Phase 0

Date: 2026-11-06 (Asia/Calcutta)

| Component | Result | Fallback / verification limit |
|---|---|---|
| Repository | Empty working directory except newly written `AGENTS.md`; no prior `.git` | Baseline Git repository initialized for Phase 0 commit. |
| Python | `python.exe` WindowsApps alias found, but launch failed with a PowerShell standard-error encoding error; `py` not found; `python3` alias inaccessible | Treat Python as UNAVAILABLE. Cannot run backend or Python dependency checks until a working interpreter is installed/configured. |
| Node | v22.19.0 | Available. |
| npm | 10.9.3 | Available. |
| PostgreSQL / psql | `psql` not found | Docker could host PostgreSQL if daemon is running, but daemon not yet probed; no DB-backed verification now. |
| Docker | v29.4.0 | CLI available. Daemon not yet verified. |
| Docker Compose | v5.1.2 | CLI available; service execution unverified pending daemon. |
| Network | DNS lookup for pypi.org failed; TCP 443 probe returned false | External downloads/source verification unavailable in this session. |
| Playwright | `playwright`, `@playwright/test`, and `puppeteer` not resolvable in Node | No browser automation or visual gate. UI gate remains UNVERIFIED until Chromium and Playwright are available. |
| Chromium | No Playwright package/browser found; no browser executable verified | No screenshot or browser journey verification. |
| gitleaks | Not found on PATH | Use a documented repository text scan at hardening; this cannot equal a dedicated secret scanner. |

Commands actually run: `git status --short --branch` (reported not a Git repository); `node --version`; `npm --version`; `docker --version`; `docker compose version`; `psql --version` (not found); Python/py/python3 version probes (launch failures); Node `require.resolve` checks for Playwright packages; `Test-NetConnection pypi.org:443` (DNS failure); `Get-Command gitleaks` (not found).
