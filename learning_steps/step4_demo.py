"""
Step 4 demo: a counter built ONLY with mini_ui.

Keep this file in the same folder as mini_ui.py.
Run:  python step4_demo.py
Open: http://localhost:8000
"""

from mini_ui import State, Div, Heading, Text, Button, run_app

# 1. The data that can change
state = State(count=0)


# 2. Event handlers: plain functions that change state
def increment():
    state.set("count", state.get("count") + 1)


def decrement():
    state.set("count", state.get("count") - 1)


def reset():
    state.set("count", 0)


# 3. The UI, described as a function of state
def build_ui():
    return Div(
        Heading("Counter"),
        Text(f"Count: {state.get('count')}"),
        Button("-1", on_click=decrement),
        Button("+1", on_click=increment),
        Button("Reset", on_click=reset),
        class_="app",
    )


# 4. Start the app
run_app(build_ui, title="Counter")
