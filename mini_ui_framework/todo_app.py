"""
To-Do Notes App - built ONLY with mini_ui.

A notes-style layout:
    Left sidebar  : all your to-do lists, with date + time of last save
    Right panel   : the selected list, where you view and edit it

Everything saves automatically (to todo_data.json) with a timestamp.

Keep this file in the same folder as mini_ui.py.
Run:  python todo_notes_app.py
Open: http://localhost:8000
"""

import json
import os
from datetime import datetime
from pathlib import Path

from mini_ui import State, Div, Heading, Text, Span, Button, Input, run_app

DATA_FILE = Path(__file__).parent / "todo_data.json"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# ===============================================================
# 1. TIME HELPERS
# ===============================================================
def now():
    return datetime.now().strftime(TIME_FORMAT)


def pretty(timestamp):
    """'2026-10-10 14:35:07' -> '10 Oct 2026 · 2:35 PM'"""
    dt = datetime.strptime(timestamp, TIME_FORMAT)
    hour = dt.strftime("%I").lstrip("0")
    return f"{dt.day} {dt:%b %Y} · {hour}:{dt:%M} {dt:%p}"


# ===============================================================
# 2. LOADING AND SAVING (the file on disk)
# ===============================================================
def default_data():
    stamp = now()
    return {
        "current": 1,
        "lists": [
            {
                "id": 1,
                "title": "My first list",
                "created": stamp,
                "updated": stamp,
                "todos": [
                    {"text": "Learn Python", "done": True},
                    {"text": "Build a UI framework", "done": False},
                ],
            }
        ],
    }


def load_data():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for lst in data["lists"]:               # make sure the file looks right
            lst["id"], lst["title"], lst["created"], lst["updated"], lst["todos"]
        return data
    except (OSError, ValueError, KeyError, TypeError):
        return default_data()


def save_data():
    """Runs automatically after EVERY state change (see state.subscribe below)."""
    data = {"current": state.get("current"), "lists": state.get("lists")}
    temp_file = DATA_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, DATA_FILE)            # safe write: never a half-written file


# ===============================================================
# 3. STATE
#    lists   = all to-do lists
#    current = id of the list shown on the right
#    title   = text in the title box (while you edit it)
#    draft   = text in the "add a task" box
# ===============================================================
data = load_data()
lists = data["lists"]
current_id = data.get("current")
if not any(lst["id"] == current_id for lst in lists):
    current_id = lists[0]["id"] if lists else None
first = next((lst for lst in lists if lst["id"] == current_id), None)

state = State(
    lists=lists,
    current=current_id,
    title=first["title"] if first else "",
    draft="",
)
state.subscribe(save_data)                      # AUTO-SAVE on every change
save_data()                                     # and save once at start-up


# ===============================================================
# 4. HELPERS THAT CHANGE THE DATA
#    We always make NEW lists/dicts instead of editing the old ones,
#    so State notices the change.
# ===============================================================
def get_current():
    for lst in state.get("lists"):
        if lst["id"] == state.get("current"):
            return lst
    return None


def sorted_lists():
    """Newest-saved list first, like a notes app."""
    return sorted(state.get("lists"), key=lambda lst: lst["updated"], reverse=True)


def edit_current(**changes):
    """Change the open list and stamp it with the current date and time."""
    new_lists = []
    for lst in state.get("lists"):
        if lst["id"] == state.get("current"):
            lst = {**lst, **changes, "updated": now()}
        new_lists.append(lst)
    state.set("lists", new_lists)


def current_todos():
    current = get_current()
    return [dict(t) for t in current["todos"]] if current else []


def commit_title():
    """Save the title box into the open list (called at the start of every handler)."""
    current = get_current()
    if current is None:
        return
    title = state.get("title", "").strip()
    if title == "":
        state.set("title", current["title"])    # empty title: put the old one back
        return
    if title != current["title"]:
        edit_current(title=title)
    state.set("title", title)


# ===============================================================
# 5. EVENT HANDLERS
# ===============================================================
def new_list():
    commit_title()
    new_id = max((lst["id"] for lst in state.get("lists")), default=0) + 1
    stamp = now()
    lst = {
        "id": new_id,
        "title": f"New list {new_id}",
        "created": stamp,
        "updated": stamp,
        "todos": [],
    }
    state.update(
        lists=state.get("lists") + [lst],
        current=new_id,
        title=lst["title"],
        draft="",
    )


def select_list(list_id):
    commit_title()                              # save any title edit first
    for lst in state.get("lists"):
        if lst["id"] == list_id:
            state.update(current=list_id, title=lst["title"], draft="")


def delete_list():
    current_id = state.get("current")
    remaining = [lst for lst in state.get("lists") if lst["id"] != current_id]
    remaining_sorted = sorted(remaining, key=lambda lst: lst["updated"], reverse=True)
    if remaining_sorted:
        state.update(
            lists=remaining,
            current=remaining_sorted[0]["id"],
            title=remaining_sorted[0]["title"],
            draft="",
        )
    else:
        state.update(lists=remaining, current=None, title="", draft="")


def add_todo():
    commit_title()
    text = state.get("draft", "").strip()
    if get_current() is None or not text:
        return                                  # nothing to add
    edit_current(todos=current_todos() + [{"text": text, "done": False}])
    state.set("draft", "")                      # clear the box


def toggle_todo(index):
    commit_title()
    todos = current_todos()
    if index < len(todos):
        todos[index]["done"] = not todos[index]["done"]
        edit_current(todos=todos)


def delete_todo(index):
    commit_title()
    todos = current_todos()
    if index < len(todos):
        del todos[index]
        edit_current(todos=todos)


def clear_done():
    commit_title()
    todos = current_todos()
    kept = [t for t in todos if not t["done"]]
    if len(kept) != len(todos):
        edit_current(todos=kept)


# ===============================================================
# 6. UI PIECES
# ===============================================================
def icon_button(icon, tip, handler, extra_class=""):
    """A round emoji button. Hovering shows the tooltip text (see CSS: data-tip)."""
    return Button(
        icon,
        on_click=handler,
        data_tip=tip,
        aria_label=tip,
        class_=("icon-btn " + extra_class).strip(),
    )


def note_card(lst):
    """One entry in the left sidebar."""
    total = len(lst["todos"])
    done = sum(1 for t in lst["todos"] if t["done"])
    is_active = lst["id"] == state.get("current")
    return Div(
        Div(lst["title"], class_="note-title"),
        Div(f"{done} of {total} done", class_="note-count"),
        Div(f"🕒 {pretty(lst['updated'])}", class_="note-meta"),
        class_="note active" if is_active else "note",
        on_click=lambda list_id=lst["id"]: select_list(list_id),
    )


def sidebar():
    cards = [note_card(lst) for lst in sorted_lists()]
    return Div(
        Div(
            Heading("📝 My Lists", level=2),
            Button("➕ New list", on_click=new_list, class_="btn-new"),
            class_="sidebar-head",
        ),
        Div(
            *(cards or [Text("No lists yet", class_="muted")]),
            class_="note-list",
            data_scroll="sidebar",
        ),
        class_="sidebar",
    )


def task_card(index, todo):
    """One task, in its own box."""
    if todo["done"]:
        toggle = icon_button("↩️", "Undo: mark as not done", lambda index=index: toggle_todo(index))
    else:
        toggle = icon_button("✅", "Mark as done", lambda index=index: toggle_todo(index))
    delete = icon_button("🗑️", "Delete this task", lambda index=index: delete_todo(index), "danger")

    return Div(
        Span(todo["text"], class_="task-text"),
        Div(toggle, delete, class_="task-actions"),
        class_="task done" if todo["done"] else "task",
    )


def panel():
    current = get_current()

    # nothing selected / no lists at all
    if current is None:
        return Div(
            Div("📭", class_="empty-icon"),
            Heading("No list selected", level=2),
            Text("Press “➕ New list” in the sidebar to get started."),
            class_="panel empty",
        )

    todos = current["todos"]
    remaining = sum(1 for t in todos if not t["done"])
    task_cards = [task_card(i, t) for i, t in enumerate(todos)]

    return Div(
        Div(
            Input(
                bind="title",
                value=state.get("title"),
                on_enter=commit_title,
                placeholder="List title",
                maxlength="60",
                class_="title-input",
            ),
            icon_button("🗑️", "Delete this whole list", delete_list, "danger"),
            class_="panel-head",
        ),
        Text(
            f"Created {pretty(current['created'])}  ·  Last saved {pretty(current['updated'])}",
            class_="stamp",
        ),
        Div(
            Input(
                bind="draft",
                value=state.get("draft"),
                on_enter=add_todo,
                placeholder="Add a new task…",
                class_="task-input",
            ),
            Button("➕ Add", on_click=add_todo, class_="btn-add", data_focus="draft"),
            class_="add-row",
        ),
        Text(f"{remaining} left  ·  {len(todos)} total", class_="summary"),
        Div(
            *(task_cards or [Text("Nothing here yet. Add your first task above ✨", class_="muted")]),
            class_="tasks",
            data_scroll=f"tasks-{current['id']}",
        ),
        Button("🧹 Clear completed", on_click=clear_done, class_="btn-clear"),
        class_="panel",
    )


def build_ui():
    return Div(sidebar(), panel(), class_="app")


# ===============================================================
# 7. STYLES (colors, fonts, layout)
# ===============================================================
APP_CSS = """
* { box-sizing: border-box; }
html, body { height: 100%; margin: 0; }

body {
  font-family: "Segoe UI", system-ui, sans-serif;
  color: #2b2d42;
  padding: 24px;
  /* bubblegum pink -> sky blue */
  background: linear-gradient(135deg, #ff9fd0 0%, #ffc6e5 35%, #a8dcff 70%, #78c3f7 100%);
  background-attachment: fixed;
}
#root { height: 100%; }
button { font-family: inherit; cursor: pointer; border: none; }
p { margin: 0; }

.app { display: flex; gap: 20px; height: 100%; max-width: 1100px; max-height: 780px; margin: 0 auto; }

/* ---------- left sidebar ---------- */
.sidebar {
  width: 300px; flex-shrink: 0; display: flex; flex-direction: column;
  background: rgba(255, 255, 255, 0.55); backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.8); border-radius: 22px;
  padding: 18px; box-shadow: 0 10px 30px rgba(80, 100, 160, 0.18);
}
.sidebar-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.sidebar-head h2 { margin: 0; font-size: 20px; }
.note-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding: 4px; }

.note {
  background: #fff; border-radius: 14px; padding: 12px 14px; cursor: pointer;
  border: 2px solid transparent;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}
.note:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(80, 100, 160, 0.2); }
.note.active { border-color: #ff6fb5; background: linear-gradient(135deg, #ffffff, #ffeaf5); }
.note-title { font-weight: 700; font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.note-count { font-size: 12px; color: #5a6a8a; margin-top: 2px; }
.note-meta { font-size: 12px; color: #6b7a99; margin-top: 6px; }

/* ---------- right panel ---------- */
.panel {
  flex: 1; min-width: 0; display: flex; flex-direction: column;
  background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.8); border-radius: 22px;
  padding: 22px 24px; box-shadow: 0 10px 30px rgba(80, 100, 160, 0.18);
}
.panel.empty { align-items: center; justify-content: center; text-align: center; gap: 8px; }
.empty-icon { font-size: 64px; }
.panel-head { display: flex; align-items: center; gap: 8px; }
.title-input {
  flex: 1; min-width: 0; font: inherit; font-size: 26px; font-weight: 700; color: #2b2d42;
  background: transparent; border: 2px solid transparent; border-radius: 10px; padding: 6px 10px;
  transition: background 0.15s, border-color 0.15s;
}
.title-input:hover { background: rgba(255, 255, 255, 0.6); }
.title-input:focus { outline: none; background: #fff; border-color: #78c3f7; }
.stamp { margin: 2px 12px 0; font-size: 13px; color: #5a6a8a; }

.add-row { display: flex; gap: 10px; margin: 16px 0 6px; }
.task-input {
  flex: 1; min-width: 0; font: inherit; font-size: 16px; padding: 12px 14px;
  border: 2px solid #cfe8ff; border-radius: 12px; background: #fff;
  transition: border-color 0.15s;
}
.task-input:focus { outline: none; border-color: #ff6fb5; }
.summary { font-weight: 600; margin: 10px 4px; color: #3d4a6b; }

/* ---------- buttons ---------- */
.btn-new, .btn-add {
  background: linear-gradient(135deg, #ff7ab8, #5ab4f5); color: #fff; font-weight: 700;
  padding: 10px 16px; border-radius: 12px; font-size: 14px;
  transition: transform 0.15s, filter 0.15s;
}
.btn-new:hover, .btn-add:hover { transform: translateY(-1px); filter: brightness(1.07); }
.btn-clear {
  align-self: flex-start; margin-top: 12px; padding: 9px 14px; border-radius: 10px;
  background: rgba(255, 255, 255, 0.85); color: #2b2d42; font-weight: 600;
  transition: background 0.15s;
}
.btn-clear:hover { background: #fff; }

/* round emoji buttons with a hover tooltip */
.icon-btn {
  position: relative; width: 38px; height: 38px; margin-left: 6px; border-radius: 50%;
  background: #f1f6ff; font-size: 18px; display: inline-flex; align-items: center; justify-content: center;
  transition: transform 0.15s, background 0.15s;
}
.icon-btn:hover { transform: scale(1.12); background: #e2efff; }
.icon-btn.danger:hover { background: #ffe0ea; }
.icon-btn::after {
  content: attr(data-tip); position: absolute; right: calc(100% + 10px); top: 50%;
  transform: translateY(-50%) scale(0.95); background: #2b2d42; color: #fff;
  font-size: 12px; font-weight: 600; padding: 6px 10px; border-radius: 8px;
  white-space: nowrap; opacity: 0; pointer-events: none; z-index: 10;
  transition: opacity 0.15s, transform 0.15s;
}
.icon-btn:hover::after { opacity: 1; transform: translateY(-50%) scale(1); }

/* ---------- task boxes ---------- */
.tasks { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding: 6px 4px; }
.task {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  background: #fff; border: 2px solid #ffd0e8; border-radius: 14px; padding: 12px 14px;
  box-shadow: 0 3px 10px rgba(255, 120, 180, 0.18);
  transition: transform 0.15s, box-shadow 0.15s;
}
.task:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(255, 120, 180, 0.28); }
.task-text {
  font-family: "Times New Roman", Times, serif;
  font-weight: 600;           /* semi-bold */
  color: #050505;             /* very dark black */
  font-size: 20px; word-break: break-word;
}
.task-actions { display: flex; flex-shrink: 0; }
.task.done { background: #f3f9ff; border-color: #cfe8ff; box-shadow: none; }
.task.done .task-text { text-decoration: line-through; text-decoration-color: #ff5aa5; text-decoration-thickness: 2px; }

.muted { color: #6b7a99; text-align: center; margin: 20px 0; }

/* ---------- small screens ---------- */
@media (max-width: 760px) {
  body { padding: 12px; }
  .app { flex-direction: column; height: auto; max-height: none; }
  .sidebar { width: 100%; max-height: 260px; }
  .panel { min-height: 520px; }
}
"""


# ===============================================================
# 8. START
# ===============================================================
if __name__ == "__main__":
    run_app(build_ui, state=state, title="To-Do Notes", css=APP_CSS)
