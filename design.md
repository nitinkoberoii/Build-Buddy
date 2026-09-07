# BuildBuddy design system

## Direction

BuildBuddy is a dark, editorial product interface: ultraviolet rings, magenta ribbons, glass panels, and calm technical typography. The landing page establishes this language; workflow screens should remain visually consistent but prioritize clear status and readable code.

## Tokens

| Token | Value | Use |
| --- | --- | --- |
| Ink | `#050408` | application background |
| Surface | `#120d18` | elevated panels |
| Glass | `rgba(37, 21, 42, .84)` | translucent cards |
| Text | `#f5eff8` | primary content |
| Muted | `#9f94a5` | supporting copy |
| Violet | `#835aff` | brand/selected state |
| Magenta | `#eb71ff` | glow/highlight |
| Success | `#7be0b8` | completed run |
| Warning | `#f2bc63` | attention required |
| Error | `#ef7d95` | failure |

## Typography and layout

- Space Grotesk: headings and wordmark.
- Manrope: body and controls.
- DM Mono: status, IDs, and code metadata.
- Spacing uses 4px increments: 8, 12, 16, 24, 32, 48, 64.
- Maximum desktop shell: 1200px; mobile gutter: 16px.

## Required screens

1. Landing and prompt submission.
2. Generation progress: prompt, stage indicator, event feed, cancel action, and recovery.
3. Result: plan summary, file tree, source preview, and ZIP download.
4. Generation history: state, title, time, reopen action.
5. Empty and error states with clear next actions.

## Interaction requirements

- Every action has immediate feedback; status is never animation-only.
- Disable duplicate create requests.
- Attachments display name, remove option, accepted types, and validation errors.
- Do not depend on hover for required actions.
- Respect reduced-motion preferences, keyboard navigation, focus visibility, and screen readers.
