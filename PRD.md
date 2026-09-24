# BuildBuddy product requirements document

## Vision

BuildBuddy is a web platform that turns an idea into an understandable, editable starter project. It makes planning and code generation visible rather than a black box.

## Users

- Indie developers starting projects.
- Designers and founders validating ideas.
- Learners inspecting project structure and code.

## Jobs to be done

1. Convert an app idea into a plan and starter implementation.
2. Observe progress and recover clearly from failure.
3. Inspect and download generated files while retaining control.

## MVP

- Validated prompt submission with optional attachment metadata.
- Supported model selection from an allowlist.
- Run lifecycle: queued, planning, architecting, coding, completed, failed, cancelled.
- SSE status with polling fallback.
- Plan/task summary, file list/preview, ZIP download, and active-session history.

## Functional requirements

| ID | Requirement |
| --- | --- |
| FR-1 | Valid prompts create a generation ID. |
| FR-2 | Users can observe run state without manually refreshing via SSE or status polling. |
| FR-3 | Each run writes only in its isolated UUID directory. |
| FR-4 | Users can access only their generation files safely. |
| FR-5 | Completed projects can be downloaded as ZIP archives. |
| FR-6 | Validation, provider, timeout, and cancellation errors are understandable. |
| FR-7 | The workflow works on current desktop and mobile browsers. |
| FR-8 | Users can request cancellation of an active generation run at any time via the UI or API. |
| FR-9 | The system performs automated self-healing retries (up to 3 attempts) for transient JSON/schema errors during planning and architecture phases. |
| FR-10 | Failed generations present a structured incident ticket (`TICKET #BB-FAIL-XXXXXXXX`) with human-understandable cause analysis, expandable diagnostic logs, and clear CTAs (`Try Again`, `Return to Home`). |
| FR-11 | Completed runs render in an interactive 35%/65% split resizable workspace container with file tree exploration, syntax-highlighted editor with line numbers, copy action, and inline edit mode. |
| FR-12 | Prompt submission is bound to the `Enter` key (`Shift+Enter` for line breaks). |
| FR-13 | Transient API and token notices trigger a bottom-right snackbar toast with an animated shrinking horizontal progress countdown indicator. |

## Non-functional requirements

- Provider keys never reach the browser.
- Validate prompt sizes, attachment type/size, model allowlist, paths, and ZIP contents.
- Support idempotent client retries and resumable status reads.
- Target fast project generation latency (~10–15 seconds total runtime).
- Use structured generation-ID logs without sensitive data.
- Maintain keyboard access, focus visibility, contrast, and reduced-motion support.

## Delivery status

- Phase 0 (Agent core): Complete.
- Phase 1 (Web landing): Complete.
- Phase 2 (FastAPI backend): Complete.
- Phase 3 (Frontend visual workspace integration, resizable containers, job cancellation, incident tickets, & snackbar toasts): Complete.
- Phase 4 (Reliability & persistence): Next.

## Out of scope for MVP

Collaborative editing, app hosting, arbitrary shell execution, marketplace templates, billing, and unrestricted repository access.

