# BuildBuddy delivery phases

## Phase 0 — agent foundation (complete)

- LangGraph Planner → Architect → Coder flow.
- Groq-backed CLI execution and scoped output tools.

## Phase 1 — web foundation (complete)

- React, TypeScript, and Vite frontend.
- Responsive product landing experience and design system.

## Phase 2 — API foundation (complete)

- FastAPI application and typed schemas.
- Reusable generation service extracted from CLI.
- UUID-scoped run storage and lifecycle events.
- Health, create, status, event, files, download, and cancel endpoints.
- Unit/API tests and OpenAPI documentation.

**Exit criterion met:** an API client can start a run, observe state, cancel if needed, and safely access output files.

## Phase 3 — frontend workflow & interactive workspace (complete)

- **Part 1 (Complete)**: API client (`api.ts`), TypeScript schemas (`types.ts`), Vite dev proxy (`vite.config.ts`), and SSE event subscription handlers.
- **Part 2 (Complete)**:
  - Progress dashboard with live terminal log and job cancellation (`LoadingScreen.tsx`).
  - Resizable split container layout (35% left container for file tree explorer, 65% right container for code editor).
  - Syntax-highlighted code editor with line numbers, copy button, and inline edit mode (`CodeViewer.tsx`).
  - Header bar with logo, brand text, project name badge, download ZIP CTA, start new project button, and user profile avatar (`NK`).
  - Self-healing LLM retry loop in agent planner and architect nodes (up to 3 auto-corrections).
  - Fast 1-pass LLM direct file generation (~10–15s total generation time).
  - Failed generation Incident Ticket UI (`TICKET #BB-FAIL-XXXXXXXX`) with human-readable error descriptions, raw log toggle, and subdued glass action buttons (`Try Again`, `Return to Home`).
  - Bottom-right snackbar toast notifications (`SnackbarToast.tsx`) with animated shrinking progress countdown line.
  - Keyboard submission binding (`Enter` key on prompt textarea).
  - Thread-Based AI Workspace Refinement Engine (`POST /api/generations/{id}/refine` & `refine_project_agent`) for incremental file updates and file creation.
  - Interactive AI edit prompt panel below file tree with scrollable thread message log (`ThreadMessage`), non-overlapping flexbox layout, and message action toolbars (`📋 Copy`, `🔄 Regenerate`, `✏️ Edit`).
  - Persistent URL Hash & Path Routing (`#/project/{id}`) enabling page reloads (`F5`), direct link sharing, and back/forward browser navigation support.

**Exit criterion met:** a browser user can submit a prompt (via click or `Enter`), monitor progress, cancel active runs, inspect generated code in a resizable split workspace, perform incremental AI file edits within a thread session, reload/bookmark workspaces via persistent URLs, recover gracefully from generation errors via incident tickets, receive transient API/token notices, and download a project without a terminal.

## Phase 4A — core platform foundation (next)

### Data, tenancy, and migrations

- Introduce SQLAlchemy 2.x models and Alembic migrations; support SQLite locally and PostgreSQL in hosted environments.
- Establish the ownership hierarchy: `users → organizations → memberships → projects → generations`.
- Persist `generation_events`, `thread_messages`, `project_snapshots`, `artifacts`, `attachments`, `sessions`, `api_keys`, `usage_records`, and append-only `audit_logs`.
- Enforce authorization on every generation, file, artifact, refinement, and download query. Never trust client-supplied ownership IDs.
- Encrypt backups and regularly test restoring the database and artifacts.

### Identity and authorization

- Provide registration, verified email, password reset, secure sessions, logout/revocation, and MFA for administrators.
- Use Argon2id password hashing; support Google/GitHub OIDC with PKCE where it is useful.
- Use short-lived access tokens and rotating, server-revocable refresh sessions in secure HTTP-only cookies; add CSRF protection for cookie-authenticated mutations.
- Implement organization roles: `owner`, `admin`, `member`, and `viewer`. Internal support access must be explicit, time-bounded, and audited.
- Add scoped, hashed, expiring API keys only after browser authentication and authorization work correctly.

### Durable execution and artifacts

- Select and document one queue stack: Redis plus ARQ **or** Redis plus Celery; do not deploy both.
- Run LangGraph jobs in workers, with idempotent enqueueing, concurrency quotas, heartbeats, cancellation propagation, dead-letter handling, and classified retry behavior.
- Keep one disposable, UUID-scoped workspace per generation. Generated code must never execute on API/worker hosts by default.
- Use S3-compatible object storage (S3 or MinIO) for ZIPs, artifacts, and snapshots; issue only short-lived, permission-checked presigned URLs.
- Snapshot a project atomically before and after every refinement so users can compare or restore prior versions.

**Exit criteria:** authenticated users can create and access only their organization’s projects; jobs survive API restarts; projects/artifacts are persisted and recoverable; each generation is isolated and cancellable.

## Phase 4B — reliability, operations, and release engineering

### Resilience and recovery

- Define maximum prompt, attachment, file-count, artifact-size, generation-time, tool-call, and token/cost limits.
- Implement job timeouts, retry/backoff policy, cancellation guards, provider outage handling, and explicit terminal states.
- Define and test backup schedule, point-in-time recovery where supported, restoration drills, RPO, and RTO.
- Add liveness, readiness, and health endpoints plus graceful API/worker shutdown.

### Observability

- Emit structured, redacted JSON logs with request, organization, user, generation, and job correlation IDs.
- Add OpenTelemetry traces across API, queue, worker, LangGraph stages, and provider calls.
- Collect metrics for API latency/errors, queue depth, job duration, completion/failure/cancel rate, token usage/cost, storage, authentication failures, and rate-limit events.
- Configure dashboards, actionable alerts, error tracking, status page, and incident communication/runbooks.

### Delivery and quality gates

- Containerize frontend, API, and worker with multi-stage Docker builds.
- Build GitHub Actions checks: Ruff/ESLint, formatting, Mypy/TypeScript, Pytest, Playwright, dependency/container scans, image build, migration test, and staging smoke test.
- Use separate development, staging, and production environments with controlled configuration/secrets and rollback-capable deployment.
- Perform load tests for concurrent generations, queue saturation, SSE reconnection, and artifact downloads.

**Exit criteria:** production deploys are repeatable and reversible; failures are observable and alertable; backups have been restored successfully; CI blocks unsafe or broken releases.

## Phase 4C — application security and AI-runtime hardening

### API and platform security

- Enforce Redis-backed rate limits by IP, account, organization, API key, and concurrency/cost quota.
- Apply strict origin-based CORS, CSP, HSTS, secure cookies, content-type/frame protections, and request/payload limits.
- Use idempotency keys for generation creation and stable error contracts with correlation IDs.
- Centralize secrets in managed secret storage; rotate provider keys and never log, return, or bundle secrets.
- Scan dependencies, source, containers, and infrastructure configuration; define vulnerability triage and patch SLAs.

### Files, agent tools, and isolation

- Validate upload type, MIME signature, size, count, and archive contents; malware-scan uploads before agent use.
- Defend against path traversal, symlinks, ZIP bombs, unsafe binaries, and secret leakage in generated artifacts.
- Enforce allowlisted provider/model IDs, prompt/file limits, tool-call budgets, command timeouts, and network restrictions.
- If code preview/execution is introduced later, use disposable sandboxes with no default network access and bounded CPU, memory, disk, processes, and wall time.
- Add AI prompt-injection tests for uploaded files and untrusted generated content.

### Audit and assurance evidence

- Create append-only, access-controlled audit events for authentication, privilege changes, project access, prompt submission, refinement, downloads, API-key changes, and support access.
- Map controls and automated evidence to OWASP ASVS and a SOC 2 readiness control matrix; do not claim certification before an independent audit.
- Complete a staged internal security review and independent penetration test before public/enterprise launch.

**Exit criteria:** security tests cover authorization, input/path safety, agent boundaries, and common abuse paths; secrets and sensitive logs are controlled; a security review finds no unresolved critical/high-risk issues.

## Phase 4D — privacy, legal, and compliance readiness

### Privacy lifecycle

- Create a data inventory and classification policy for identities, prompts, uploads, generated projects, logs, artifacts, backups, and telemetry.
- Document purpose, lawful basis where relevant, retention period, location, processor, and deletion procedure for every data category.
- Implement user-facing access, export, deletion, and account-closure flows; include project/artifact deletion and backup-expiry handling.
- Minimize sensitive prompt data in logs/traces; redact PII/secrets and assess whether a DPIA/AI risk assessment is required.
- Maintain data-residency and cross-border transfer decisions before entering affected markets.

### Legal, vendors, and incident management

- Publish Terms of Service, Privacy Notice, Cookie Notice, Acceptable Use Policy, and support/security contact process.
- Maintain a vendor/subprocessor register, security-review workflow, data processing agreements, and customer DPA process.
- Implement consent/preferences controls where required by tracking or marketing choices.
- Write and exercise incident response, breach assessment, customer notification, business continuity, and disaster recovery playbooks.
- Build SOC 2 readiness evidence across security, availability, confidentiality, processing integrity, and privacy according to target customer needs; assess ISO 27001 only when commercially justified.

**Exit criteria:** published policies reflect the actual system; deletion/export/retention controls work; vendor and incident processes are operational; compliance evidence collection has started and has named owners.

## Phase 5 — launch, billing, and iteration

- Integrate a payment provider so BuildBuddy does not store card data; add plans, quotas, usage metering, invoices, and entitlement enforcement.
- Create support operations, account recovery, admin tooling, and documented service targets.
- Release through internal, beta, and staged/canary cohorts with rollback and communication plans.
- Use product analytics that respect privacy preferences; collect customer feedback and measure generation quality, cost, latency, safety, and retention.
- Operate a continuing model/provider evaluation program with regression tests, spend controls, and quality gates.

**Exit criteria:** paying users can onboard and receive support safely; quotas/billing are enforced; rollout health is measurable; the team can operate, improve, and recover the platform continuously.
