// app.js
// Simple Todo List Application

// Task model
class Task {
    constructor(id, title, completed = false) {
        this.id = id;
        this.title = title;
        this.completed = completed;
    }
}

// Task Manager handles CRUD and persistence
class TaskManager {
    constructor() {
        this.tasks = [];
        this.loadFromStorage();
    }

    addTask(title) {
        const id = Date.now();
        const task = new Task(id, title);
        this.tasks.push(task);
        this.save();
    }

    editTask(id, newTitle) {
        const t = this.tasks.find(t => t.id === id);
        if (t) {
            t.title = newTitle;
            this.save();
        }
    }

    deleteTask(id) {
        this.tasks = this.tasks.filter(t => t.id !== id);
        this.save();
    }

    toggleComplete(id) {
        const t = this.tasks.find(t => t.id === id);
        if (t) {
            t.completed = !t.completed;
            this.save();
        }
    }

    filterTasks(filter) {
        return this.tasks.filter(t => {
            if (filter === 'all') return true;
            if (filter === 'active') return !t.completed;
            if (filter === 'completed') return t.completed;
            return true;
        });
    }

    loadFromStorage() {
        const data = localStorage.getItem('todoTasks');
        this.tasks = data ? JSON.parse(data) : [];
    }

    save() {
        localStorage.setItem('todoTasks', JSON.stringify(this.tasks));
    }
}

// UI Functions
const taskListEl = document.getElementById('task-list');
const taskFormEl = document.getElementById('task-form');
const newTaskInputEl = document.getElementById('new-task-input');
const filterButtons = document.querySelectorAll('.filter-btn');

let currentFilter = 'all';

function renderTasks(filter = 'all') {
    const tasks = manager.filterTasks(filter);
    taskListEl.innerHTML = '';
    tasks.forEach(task => {
        const li = document.createElement('li');
        li.className = 'task-item' + (task.completed ? ' completed' : '');
        li.dataset.id = task.id;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'task-checkbox';
        checkbox.checked = task.completed;

        const titleSpan = document.createElement('span');
        titleSpan.className = 'task-title';
        titleSpan.textContent = task.title;

        const editBtn = document.createElement('button');
        editBtn.className = 'edit-btn';
        editBtn.textContent = 'Edit';

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.textContent = 'Delete';

        li.appendChild(checkbox);
        li.appendChild(titleSpan);
        li.appendChild(editBtn);
        li.appendChild(deleteBtn);

        taskListEl.appendChild(li);
    });
}

function updateFilterButtons(activeFilter) {
    filterButtons.forEach(btn => {
        if (btn.dataset.filter === activeFilter) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function attachEventListeners() {
    // Add task
    taskFormEl.addEventListener('submit', e => {
        e.preventDefault();
        const title = newTaskInputEl.value.trim();
        if (title) {
            manager.addTask(title);
            newTaskInputEl.value = '';
            renderTasks(currentFilter);
        }
    });

    // Filter buttons
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            currentFilter = btn.dataset.filter;
            renderTasks(currentFilter);
            updateFilterButtons(currentFilter);
        });
    });

    // Task list events (delegation)
    taskListEl.addEventListener('click', e => {
        const li = e.target.closest('li');
        if (!li) return;
        const id = Number(li.dataset.id);

        if (e.target.classList.contains('delete-btn')) {
            manager.deleteTask(id);
            renderTasks(currentFilter);
        } else if (e.target.classList.contains('edit-btn')) {
            // Switch to edit mode
            const titleSpan = li.querySelector('.task-title');
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'edit-input';
            input.value = titleSpan.textContent;
            li.replaceChild(input, titleSpan);
            input.focus();

            const saveEdit = () => {
                const newTitle = input.value.trim();
                if (newTitle) {
                    manager.editTask(id, newTitle);
                }
                renderTasks(currentFilter);
            };

            input.addEventListener('blur', saveEdit);
            input.addEventListener('keydown', ev => {
                if (ev.key === 'Enter') {
                    ev.preventDefault();
                    input.blur();
                }
            });
        } else if (e.target.classList.contains('task-checkbox')) {
            manager.toggleComplete(id);
            renderTasks(currentFilter);
        }
    });
}

// Initialize
const manager = new TaskManager();
renderTasks(currentFilter);
updateFilterButtons(currentFilter);
attachEventListeners();
