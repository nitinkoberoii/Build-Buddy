# BuildBuddy design system

## Direction

BuildBuddy is a dark, editorial product interface: ultraviolet rings, magenta ribbons, glass panels, and calm technical typography. The landing page establishes this language; workflow screens remain visually consistent, clean, and distraction-free.

## Tokens

| Token | Value | Use |
| --- | --- | --- |
| Ink | `#050408` | application background |
| Surface | `#120d18` | elevated panels |
| Glass | `rgba(37, 21, 42, .84)` | translucent cards & panels |
| Text | `#f5eff8` | primary content |
| Muted | `#9f94a5` | supporting copy |
| Violet | `#835aff` | brand/selected state |
| Subdued Violet | `rgba(131, 90, 255, 0.2)` | subdued glass CTA backgrounds (`.retry-btn`) |
| Magenta | `#eb71ff` | glow/highlight |
| Success | `#7be0b8` | completed run |
| Warning | `#f2bc63` | attention required |
| Error | `#ef7d95` | failure / incident tickets |

## Typography and layout

- Space Grotesk: headings and wordmark.
- Manrope: body and controls.
- DM Mono: status, ticket IDs, line numbers, and code metadata.
- Spacing uses 4px increments: 8, 12, 16, 24, 32, 48, 64.
- Maximum desktop shell: 1200px; mobile gutter: 16px.

## UI Screens & Layout Specifications

### 1. Landing & Prompt Screen (`App.tsx`)
- Navigation header (Logo, nav links), Hero prompt section with model selector, attachment pill, press `Enter` to submit prompt, feature grids, and footer.

### 2. Loading & Terminal Progress Screen (`LoadingScreen.tsx`)
- Stage progress tracker (`planning → architecting → coding`), live SSE terminal log box, active cancellation button (`Cancel Generation`).
- **Isolated Layout**: No landing page navigation header or footer displayed.

### 3. Failed Generation Incident Ticket (`LoadingScreen.tsx`)
- Triggered on generation errors or 0 files created.
- Renders `TICKET #BB-FAIL-XXXXXXXX` header badge, human-readable root cause explanation, expandable raw diagnostic logs toggle, and subdued glass action buttons (`.retry-btn` with dark violet glass styling).

### 4. Resizable Split Workspace Container (`ProjectWorkspace.tsx`)
- **Top Header Bar**: Logo, brand title, Project Name badge, Download .ZIP CTA, "＋ Start New Project" button, and user profile avatar (`NK`). No landing header/footer present.
- **Split Containers**: 35% left container (`FileTree.tsx`) and 65% right container (`CodeViewer.tsx`).
- **Resizer Gutter (`.resizer-gutter`)**: Interactive mouse drag handle allowing real-time container width adjustments.
- **Code Editor (`CodeViewer.tsx`)**: Header badges for file path and language, copy code button, edit mode toggle, line numbers gutter, custom dark scrollbar, and live editable code text area.

### 5. Snackbar Toast Notifications (`SnackbarToast.tsx`)
- Positioned at fixed bottom-right (`bottom-6 right-6`).
- Displays icon, title, message, close button, and an animated shrinking horizontal line indicator (`.snackbar-progress-bar`).

## Interaction requirements

- Every action has immediate feedback; status is never animation-only.
- Disable duplicate create requests.
- Pressing `Enter` in the prompt textarea submits the form; `Shift+Enter` inserts line breaks.
- Attachments display name, remove option, accepted types, and validation errors.
- Do not depend on hover for required actions.
- Respect reduced-motion preferences, keyboard navigation, focus visibility, and screen readers.
