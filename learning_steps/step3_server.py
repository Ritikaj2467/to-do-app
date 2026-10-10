"""
Mini UI Framework - Step 3 (part 2)
The UI now reads from State. When state changes, the page changes.

Keep these files in the SAME folder:
    step1_mini_ui.py, step3_state.py, step3_server.py

Run:  python step3_server.py
Open: http://localhost:8000

NOTE: the "+1" / "Reset" links below are a TEMPORARY way to change state,
just to see it working. In Step 4 we replace them with real button events.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer

from step1_mini_ui import Element, Div, Heading, Text, List, Item, render
from step3_state import State


# ---------------------------------------------------------------
# 1. The app's state (all the data that can change)
# ---------------------------------------------------------------
state = State(
    count=0,
    todos=["Learn Python", "Build a framework"],
)

# Runs every time state changes (Step 4 will use this to trigger a re-render)
state.subscribe(lambda: print("State changed:", state._data))


# ---------------------------------------------------------------
# 2. A small Link helper (temporary, for this step only)
# ---------------------------------------------------------------
def Link(label, href, **props):
    return Element("a", label, href=href, **props)


# ---------------------------------------------------------------
# 3. The UI is a function of state: same state -> same UI
# ---------------------------------------------------------------
def build_ui():
    return Div(
        Heading("My First UI"),
        Text(f"Count: {state.get('count')}"),
        Link("+1", "/bump"),
        Text(" "),
        Link("Reset", "/reset"),
        List(*[Item(todo) for todo in state.get("todos")]),
        class_="app",
    )


def build_page():
    body = render(build_ui())
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mini UI</title>
</head>
<body>{body}</body>
</html>"""


# ---------------------------------------------------------------
# 4. Request handler
# ---------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_html(build_page())

        elif self.path == "/bump":
            state.set("count", state.get("count") + 1)   # change state
            self.redirect("/")                           # go back to the page

        elif self.path == "/reset":
            state.set("count", 0)
            self.redirect("/")

        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 - Page not found")

    def send_html(self, text):
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_response(303)              # 303 = "go look at this other URL"
        self.send_header("Location", location)
        self.end_headers()


def run(host="localhost", port=8000):
    server = HTTPServer((host, port), Handler)
    print(f"Server running at http://{host}:{port}  (Ctrl + C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    run()
