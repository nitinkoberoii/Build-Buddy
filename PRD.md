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
| FR-2 | Users can observe run state without manually refreshing. |
| FR-3 | Each run writes only in its isolated directory. |
| FR-4 | Users can access only their generation files. |
| FR-5 | Completed projects can be downloaded as ZIP archives. |
| FR-6 | Validation, provider, timeout, and cancellation errors are understandable. |
| FR-7 | The workflow works on current desktop and mobile browsers. |

## Non-functional requirements

- Provider keys never reach the browser.
- Validate prompt sizes, attachment type/size, model allowlist, paths, and ZIP contents.
- Support idempotent client retries and resumable status reads.
- Use structured generation-ID logs without sensitive data.
- Maintain keyboard access, focus visibility, contrast, and reduced-motion support.

## Out of scope for MVP

Collaborative editing, app hosting, arbitrary shell execution, marketplace templates, billing, and unrestricted repository access.
