# SmartTrainer — Structured Testing Prompt for Antigravity

> **Scope note:** All security/robustness testing described here targets a **local, isolated copy** of the project (Docker Compose or local venv), never the public deployment at `smart-fitness-trainer.streamlit.app`. Never run scanners, fuzzers, or load tests against infrastructure you don't own/control.

---

## 0. Paste this as the agent's operating prompt

```
You are acting as a QA + application-hardening engineer for the SmartTrainer
project located at D:\SmartTrainer. Your job has two tracks, run in this order:

TRACK A — Functional End-to-End QA
TRACK B — Security & Robustness Testing (own app, isolated local environment only)

Ground rules:
1. Only operate against localhost / a local Docker network. Never touch
   the public URL https://smart-fitness-trainer.streamlit.app or the
   real Supabase project — use a throwaway/test Supabase project or a
   mocked DB layer.
2. Every test must produce a machine-readable result (pass/fail, status
   code, latency, error trace) that can be aggregated into statistics.
3. For every finding, classify it as: Functional Bug | Reliability Issue |
   Security Weakness, with severity (Critical/High/Medium/Low), repro
   steps, and a suggested fix — not an exploitation walkthrough.
4. Produce a final report: docs/TEST_REPORT.md with pass/fail counts,
   coverage %, response-time percentiles, and an open-issues table.
5. Isolate the environment first (Section 1) before running anything else.
```

---

## 1. Environment isolation (do this first)

| Step | Command / Action | Purpose |
|---|---|---|
| 1 | `docker network create smarttrainer-test` | Isolated network, no bridge to host services |
| 2 | Spin up via `docker-compose.yml` with a **test** `.env` (fake Supabase project, `CORS_ORIGINS=http://localhost:3000`) | Never point at prod DB |
| 3 | `docker ps` + `docker port <container>` | Confirm only intended ports are published |
| 4 | Snapshot container filesystem (`docker diff`) before/after fuzzing | Detect unexpected file writes |
| 5 | Run everything with resource limits (`--memory=1g --cpus=1`) | Prevents a runaway test (e.g. video loop) from taking down your machine |

### Expected/likely local ports for this stack
Confirm these against your actual `docker-compose.yml` / `Dockerfile` / `Dockerfile.api` rather than assuming:

| Service | Default port | Check |
|---|---|---|
| Streamlit app | 8501 | `netstat -ano \| findstr 8501` (Win) or `lsof -i :8501` |
| FastAPI (`api/main.py`, Uvicorn) | 8000 | same, port 8000 |
| Next.js frontend | 3000 | same, port 3000 |
| Supabase local (if using `supabase start`) | 54321 (API), 54322 (DB), 54323 (Studio) | `supabase status` |

Use **nmap against localhost/the Docker network only**, e.g.:
```
nmap -sV -p- 127.0.0.1
```
Anything open beyond the four above (e.g. a stray dev server, exposed DB port, debugger port) is a finding — "unexpected open port" — log it with the process name (`lsof -i :<port>`).

---

## 2. Recommended local toolchain (all free/open-source, run locally)

| Purpose | Tool | Notes |
|---|---|---|
| API functional testing | Postman/Newman or `pytest` + `httpx` | Automate `/health`, `/api/history`, `/api/nutrition`, `/api/supplements`, `/api/analyze-video` |
| Load/perf testing | `locust` or `k6` | Concurrency on `/api/analyze-video` (CPU-heavy, MediaPipe) |
| Static security lint (Python) | `bandit -r core/ api/` | Flags unsafe patterns (eval, subprocess, hardcoded secrets) |
| Dependency vuln scan | `pip-audit` / `safety check` (Python), `npm audit` (frontend) | Run against `requirements.txt` and `frontend/package.json` |
| Web app scanning | OWASP ZAP (baseline scan, local target only) | Point only at `localhost:8501` / `localhost:3000` |
| Container image scan | `trivy image <image>` | Checks base image + OS package CVEs |
| Secrets scan | `gitleaks detect` or `truffleHog` | Run against the repo before any push, catches leaked keys |
| Port/service inventory | `nmap` (localhost only) | See table above |
| Coverage | `pytest --cov` (you already have a `tests/` folder) | Extend to `api/main.py`, which currently has none |

Install once, isolated:
```bash
pip install pytest pytest-cov httpx bandit pip-audit locust
npm install -g newman
```

---

## 3. TRACK A — Functional End-to-End QA

### 3.1 Userflow matrix (Streamlit)

| Flow | Cases |
|---|---|
| Signup | valid, password <8 chars, mismatched confirm, duplicate email, empty fields |
| Login | valid, wrong password, non-existent email, session expiry mid-use |
| Google OAuth | full redirect round trip, user cancels consent, code reused twice, missing `verifier` |
| Navigation | all 6 pages reachable post-login; direct URL access to a page pre-login redirects to auth |
| Logout | all `st.session_state` keys cleared; back-button after logout doesn't restore session |

### 3.2 Userflow matrix (Next.js)

| Flow | Cases |
|---|---|
| All routes | `/`, `/history`, `/live-trainer`, `/nutrition`, `/video-analysis`, `/supplements`, `/yoga` — load with backend up and backend down |
| Error states | `fetchWithHandling` network-failure message renders correctly, not a raw stack trace |
| No-auth gap | Confirm/document whether this frontend intentionally has no login (product decision, not a bug per se, but should be explicit) |

### 3.3 Backend API functional cases (`api/main.py`)

| Endpoint | Cases |
|---|---|
| `/health` | 200 always, used in uptime checks |
| `/api/history` | with/without `exercise` filter, `limit` boundary (0, negative, huge), **verify it returns real per-user data — see known issue below** |
| `/api/nutrition` | valid combo, age=0, negative weight/height, unknown `gender`/`activity_level`/`goal` strings → expect 400 not 500 |
| `/api/supplements` | static data returns correctly |
| `/api/analyze-video` | valid mp4/mov/avi/mkv, wrong extension, 0-byte file, file with wrong extension but valid video bytes, >100MB file, corrupted video (opens but 0 readable frames), unknown `exercise` key, yoga vs rep-exercise branch, temp file cleanup on both success and forced exception |

**Known architectural issue to explicitly verify in Track A:** `/api/history` calls `db.get_history(..., user_id=DEVELOPMENT_USER_ID)`, but `get_history()` never filters by that parameter — it relies on Supabase RLS via a session-authenticated client. That client is built from `st.session_state`, which does not exist in a FastAPI request context. Write a test that confirms exactly what comes back today (empty list? error? all-public rows?) and treat the answer as a **P1 functional bug**, not a hypothetical.

### 3.4 Data/session integrity

- Exercise switch mid-Streamlit-session doesn't leak previous exercise's rep data into the new session.
- `save_rep()`'s background thread doesn't drop reps under rapid rep-completion (stress with a scripted synthetic pose sequence).
- CSV export (`session.export_csv()`) matches DB-recorded totals.

---

## 4. TRACK B — Security & Robustness Testing (local isolated env only)

Frame every test as: *"does this weakness exist, how would I confirm it safely locally, how do I fix it"* — not as an attack script.

| Category | What to check | How (local, safe) |
|---|---|---|
| AuthN/AuthZ | Can FastAPI endpoints be reached without any credential and return another user's data? | Automated test hitting `/api/history` with different Supabase test-user JWTs/sessions, confirm isolation |
| CORS | Does the API accept requests from an origin outside `CORS_ORIGINS`? | `curl -H "Origin: http://evil.local" -I http://localhost:8000/api/history` against your local instance |
| File upload handling | Does `/api/analyze-video` validate content, not just extension? Can a non-video file with a `.mp4` name reach `cv2.VideoCapture`? | Upload a renamed text file, a zip bomb-sized file (within the 100MB cap), confirm graceful 400 not a crash/hang |
| Resource exhaustion | Concurrent large-video uploads — does the process OOM or hang since MediaPipe processing isn't queued/rate-limited beyond `check_upload_limit`? | `locust` with N concurrent uploads against local container with memory cap set |
| Secrets hygiene | Any hardcoded keys/tokens in repo (`gitleaks`), `.env`/`secrets.toml` committed by mistake | Static scan, already have `.env.example`/`secrets.toml.example` as good pattern — verify real files are gitignored |
| Dependency CVEs | Outdated packages in `requirements.txt` / `package.json` with known CVEs | `pip-audit`, `npm audit` |
| Error handling / info leakage | Do 500 responses leak stack traces or internal paths? | Trigger forced exceptions (bad video, DB down) locally, inspect response body |
| Rate limiting | Is `check_upload_limit` (5/hour) actually enforced end-to-end, or bypassable by omitting `user_id`? | Local test hitting `/api/analyze-video` >5 times without a valid session |
| Container hardening | Does the Docker image run as root? Unnecessary exposed ports? | `docker inspect`, `trivy image` |

---

## 5. Statistics & reporting template

Have the agent populate this after each run — this gives you the "documented with statistics" output you asked for:

```markdown
# TEST_REPORT.md — SmartTrainer

## Run metadata
- Date/time:
- Environment: local Docker / isolated network
- Git commit hash:

## Functional QA (Track A)
| Suite | Total cases | Passed | Failed | Pass rate |
|---|---|---|---|---|
| Streamlit userflow | | | | |
| Next.js userflow | | | | |
| FastAPI endpoints | | | | |
| Data/session integrity | | | | |

## Performance (from locust/k6)
| Endpoint | p50 latency | p95 latency | Error rate | Max concurrent handled |
|---|---|---|---|---|
| /api/analyze-video | | | | |
| /api/history | | | | |

## Security/robustness (Track B)
| Category | Checked | Findings | Severity |
|---|---|---|---|
| AuthZ isolation | Y/N | | |
| CORS | Y/N | | |
| File upload validation | Y/N | | |
| Resource exhaustion | Y/N | | |
| Secrets scan | Y/N | | |
| Dependency CVEs | Y/N | | |
| Error/info leakage | Y/N | | |
| Rate limiting | Y/N | | |
| Container hardening | Y/N | | |

## Open ports (local instance only)
| Port | Service | Expected? |
|---|---|---|

## Issues log
| ID | Title | Type | Severity | Repro | Suggested fix | Status |
|---|---|---|---|---|---|---|
```

---

## 6. Suggested execution order for the agent

1. Isolate environment (Section 1), confirm port inventory.
2. Run static scans (bandit, pip-audit, npm audit, gitleaks) — cheapest, no runtime needed.
3. Run Track A functional suite (extend `tests/` with a new `test_api_main.py`).
4. Run Track B checks against the same running local stack.
5. Run `locust`/`k6` load test last (most resource-intensive).
6. Aggregate everything into `TEST_REPORT.md` using the template above.
7. Triage findings by severity, propose fixes as PRs/diffs — not just a list.
