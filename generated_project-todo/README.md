# TODO List Application

A lightweight, client‑side **Todo List** built with plain HTML, CSS and JavaScript. It demonstrates the core CRUD (Create, Read, Update, Delete) operations, filtering of tasks, and persistence using the browser’s `localStorage` API.

---

## Tech Stack
- **HTML5** – Markup structure
- **CSS3** – Styling and layout (no external frameworks)
- **Vanilla JavaScript** – Application logic and DOM manipulation
- **localStorage** – Client‑side persistence

---

## Features
- **Add** new tasks via an input field or the *Add* button.
- **Edit** existing tasks by double‑clicking the task text.
- **Delete** tasks with the trash icon.
- **Filter** tasks by status: *All*, *Active*, *Completed*.
- **Persist** tasks across page reloads and browser restarts using `localStorage`.
- **Responsive** design that works on desktop and mobile browsers.

---

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/todo-app.git
   ```
2. Navigate into the project folder and open `index.html` in your browser. No build step is required.

---

## Usage
| Action | How to perform it | Notes |
|--------|-------------------|-------|
| **Add** | Type a task in the input field and press **Enter** or click the **Add** button. | The task appears in the list immediately. |
| **Edit** | Double‑click a task to turn it into an editable input. Press **Enter** or click outside to save. | Changes are saved automatically. |
| **Delete** | Click the trash icon next to a task. | The task is removed from the list and storage. |
| **Filter** | Click one of the filter buttons (*All*, *Active*, *Completed*). | Only tasks matching the selected status are shown. |

All changes are automatically written to `localStorage`, so closing the browser or reloading the page will preserve your list.

---

## How Persistence Works
The application stores the entire task list as a JSON string under the key `todoTasks` in `localStorage`. On page load, it reads this key, parses the JSON, and renders the tasks. Whenever a task is added, edited, or deleted, the updated array is stringified and written back to `localStorage`. This approach keeps the data local to the user’s browser and requires no backend.

---

## Contributing
Pull requests are welcome! If you plan a major change, please open an issue first to discuss.

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-xyz`.
3. Commit your changes: `git commit -am 'Add feature xyz'`.
4. Push to the branch: `git push origin feature-xyz`.
5. Open a Pull Request.

Please keep the code style consistent with the existing files and run any tests before submitting.

---

## License
This project is licensed under the MIT License.
