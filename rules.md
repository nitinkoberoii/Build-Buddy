# Rules for AI agents and contributors

## Before work

1. Read `architecture.md`, `design.md`, `memory.md`, and the relevant project phase.
2. Inspect existing code and preserve unrelated user changes.
3. State assumptions that materially affect scope, security, or UX.

## Code boundaries

1. Keep React work in `frontend/` and use strict TypeScript plus accessible semantic components.
2. Keep API routes thin: validate, call a service, and return typed responses.
3. Keep LangGraph execution separate from API handlers and preserve existing Python logic unless intentionally changed.
4. Invoke LangChain `@tool` objects with explicit dictionary payloads (e.g. `tool.invoke({"path": ..., "content": ...})`) rather than `.run()` positional arguments.
5. Never expose raw filesystem paths, commands, provider keys, or server environment values to the client.
6. Every web generation requires a UUID-scoped directory; never serve concurrent jobs from `generated_project-todo/`.

## UI & Visual Standards

1. Keep loading screens and workspace views isolated — do not render landing page navbars or landing footers over workspace views.
2. Use subdued glass styling for primary error recovery actions (`.retry-btn`) rather than harsh neon backgrounds.
3. Ensure line numbers, path metadata, and ticket identifiers use DM Mono typography.
4. Bind primary form submission to the `Enter` key on text inputs (`Shift+Enter` for multiline breaks).

## Security

1. Secrets must stay server-side and never be logged, committed, returned, or bundled.
2. Validate all API input with typed schemas and limits.
3. Normalize/validate all paths before reading, writing, serving, or archiving files.
4. Allowlist model providers and IDs.
5. Add rate limits and known-origin CORS before public deployment.
6. Treat generated code and user uploads as untrusted. Never execute them on API or worker hosts; any future execution requires a disposable, resource-limited sandbox.
7. Enforce organization ownership in server queries, never from a client-supplied user or project identifier.
8. Do not claim SOC 2, ISO 27001, GDPR, or other compliance certification without legal review, implemented controls, and—where applicable—independent assessment.

## Quality

1. Test validation, state transitions, error paths, and path safety with API work.
2. Run `npm run build` for frontend changes and relevant Python tests/type checks for backend changes.
3. Avoid dependencies unless they add clear value.
4. Keep UI responsive, keyboard-operable, screen-reader labelled, and reduced-motion friendly.
5. Do not label an unimplemented integration as live.

## Documentation

1. Update README for setup or public behavior changes.
2. Update architecture for API/data/storage changes.
3. Update memory after milestones with limitations and next work.
4. Update phases when an exit criterion is reached.
