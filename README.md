# Mini UI: a tiny UI framework in Python

A small UI framework written in **pure Python** (no third-party packages) that lets a developer describe a user interface as a tree of Python objects and turns it into a working web frontend. It comes with a demo app, **To-Do Notes**, built *only* with the framework.

> Built for **GDGoC Technical Task 2: Build Your Own UI Framework**.

| | |
|---|---|
| **GitHub repo** | https://github.com/Ritikaj2467/to-do-app |
| **Demo video** | _add link here_ |
| **Deployed prototype** | Not deployed (runs locally with one command) |

---

## Quick start

Requirements: **Python 3.8+**. Nothing else to install.

```bash
python todo_notes_app.py
```

Then open **http://localhost:8000** in your browser. Press `Ctrl + C` in the terminal to stop.

---

## How a UI is described

A UI is a tree of elements with props. Event handlers are plain Python functions.

```python
from mini_ui import State, Div, Heading, Text, Button, run_app

state = State(count=0)

def increment():
    state.set("count", state.get("count") + 1)

def build_ui():
    return Div(
        Heading("Counter"),
        Text(f"Count: {state.get('count')}"),
        Button("+1", on_click=increment),
    )

run_app(build_ui)
```

The UI is a **function of state**: when the state changes, `build_ui()` runs again and the page updates.

---

## How it works

```
Click / Enter key
      │
      ▼
Browser sends  POST /event/<id>  (plus the text typed in inputs)
      │
      ▼
Server saves input text into State  →  runs your handler function
      │
      ▼
State changes  →  UI is re-rendered  →  new HTML is sent back  →  page updates
```

1. **Element tree:** `Div(Button(...), Text(...))` creates `Element` objects with a tag, children and props.
2. **Renderer:** `render()` walks the tree recursively and produces an HTML string. Text is HTML-escaped, `class_` becomes `class`, and handlers like `on_click=fn` are given ids (`data-click="e0"`) so a click can be matched to its function.
3. **State:** `State` stores data and calls its subscribers whenever a value really changes.
4. **Events:** a click (or Enter key) sends the event id to the server, which runs the matching Python function and re-renders.
5. **Server:** built on Python's standard `http.server`. The framework adds a few lines of browser code that only forward events and keep scroll position and focus.

---

## Task requirements → where they are implemented

| Requirement | Implementation (`mini_ui.py`) |
|---|---|
| 1. Describe components as a tree of elements with props | `Element`, `Div`, `Heading`, `Text`, `Span`, `Button`, `Input`, `List`, `Item` |
| 2. A renderer that produces HTML | `render()` |
| 3. State handling: data changes, UI updates | `State` (`get`, `set`, `update`, `subscribe`) and re-render in `run_app()` |
| 4. Event handling: click → state change → re-render | `on_click`, `on_enter`, `bind`, and `POST /event/<id>` in `run_app()` |
| 5. A demo app built only with the framework | `todo_notes_app.py` (plus `step4_demo.py`, a counter, and `step5_todo_app.py`, a simple to-do list) |

### Framework features

- **Props:** any HTML attribute can be passed as a prop. `class_` becomes `class`, `data_tip` becomes `data-tip`, and `True`/`False`/`None` values are handled.
- **`on_click=` / `on_enter=`:** attach a Python function to a click or the Enter key.
- **`bind="name"` on `Input`:** copies typed text into `state["name"]`, so inputs keep their value across re-renders.
- **`state.subscribe(fn)`:** run code after every state change (the demo uses it for auto-save).
- **`run_app(build_ui, state=..., css=...)`:** serves the app and accepts your own stylesheet.

### Safety basics

- All text is HTML-escaped, so typing `<b>` shows `<b>` instead of breaking the page.
- The server only accepts input values for inputs that exist in the UI.
- Request bodies over 100 KB are rejected.
- Data is saved with a safe write (temp file, then replace), so the file is never half-written.

---

## Demo app: To-Do Notes

A notes-style to-do app, built only with `mini_ui`.

- **Left sidebar:** all saved lists with their last-saved date and time. Click a list to open it.
- **Right panel:** view and edit the selected list: rename it, add tasks, mark them done, delete them, clear completed ones.
- **Each task has its own box**, and a new box appears as soon as you add a task.
- **Emoji buttons with hover tooltips:** ✅ mark done, ↩️ undo, 🗑️ delete.
- **Auto-save:** every change is saved to `todo_data.json` with a timestamp, so lists are still there after a restart.
- **Keyboard:** press Enter to add a task or save a title.

---

## Project structure

```
.
├── mini_ui.py            # the framework (elements, renderer, state, server)
├── todo_notes_app.py     # demo app: To-Do Notes
├── step4_demo.py         # small example: counter
├── step5_todo_app.py     # small example: simple to-do list
├── README.md
└── .gitignore
```

---

## Limitations (honest notes)

- **State is shared.** There is one state for the whole server, so everyone who opens the page sees the same data. This is fine for a demo, and per-user sessions would be a next step.
- **Whole-UI re-render.** After every event the full UI is rebuilt and sent back. This is simple and easy to follow, but not as efficient as a virtual DOM.
- **A little browser code.** The framework adds a short script that forwards clicks and Enter presses to Python. The app code itself is 100% Python.
- **Not deployed.** It runs locally with `python todo_notes_app.py`.

## Ideas for the future

- Per-user sessions
- Editing task text in place
- Updating only the parts of the page that changed
- More components (checkboxes, dropdowns, forms)

---

## About the author

**Ritika Jain**: CSB, 1st year

- Email: [ritikaj646@gmail.com](mailto:ritikaj646@gmail.com)
- LinkedIn: [linkedin.com/in/ritika-jain2467](https://www.linkedin.com/in/ritika-jain2467)
