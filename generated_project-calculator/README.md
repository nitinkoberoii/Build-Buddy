# Simple Web Calculator

A lightweight, browser‑only calculator built with vanilla JavaScript, HTML and CSS. It runs entirely in the browser – no server, no build step, no dependencies. Just open the `index.html` file in a modern browser and start calculating.

## Project Overview
The **Simple Calculator** is designed to provide a quick, reliable way to perform basic arithmetic operations without leaving the browser. It is ideal for developers who want a minimal, dependency‑free example of a calculator, and for users who need a fast, responsive tool.

## Setup & Run
1. Clone or download the repository.
2. Open `index.html` in any modern browser (Chrome, Firefox, Edge, Safari, etc.).
3. The calculator is ready to use.

## Usage Guide
### Button Functions
| Button | Action |
|--------|--------|
| `0–9` | Append digit |
| `.` | Append decimal point |
| `+`, `-`, `×`, `÷` | Set the operation |
| `C` | Clear the current entry |
| `←` | Delete the last digit |
| `=` | Compute the result |

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `0–9` | Append digit |
| `.` | Append decimal point |
| `+`, `-`, `*`, `/`, `÷` | Choose operation |
| `Enter` or `=` | Compute |
| `Backspace` | Delete last digit |
| `c` or `C` | Clear |

### Division‑by‑Zero Handling
If a division by zero is attempted, the display shows an `Error` message and the calculator resets the current operation.

## Features
- **Basic arithmetic**: addition, subtraction, multiplication, division.
- **Responsive UI**: works on desktop and mobile browsers.
- **Clear / delete**: reset the calculator or remove the last digit.
- **Keyboard support**: type numbers and operators directly.
- **Division‑by‑zero error handling**: displays an `Error` message.

## Tech Stack
- **HTML** – structure
- **CSS** – minimal styling and responsive layout
- **JavaScript** – calculator logic

## File Structure
```
├─ index.html          # UI markup
├─ style.css           # Styling
├─ script.js           # Calculator logic
└─ README.md           # Project documentation
```

---

**Author:** Your Name
**License:** MIT