"""
mini_ui.py - your tiny UI framework

1. Elements   : describe a UI as a tree (Div, Button, Text, Input, ...)
2. Renderer   : turn the tree into HTML, register on_click / on_enter handlers
                and bound inputs
3. State      : holds data and notifies listeners when it changes
4. run_app    : serves the page, runs handlers, copies typed text into state

The flow of one click (or Enter key):
    Click -> browser sends input values + POST /event/<id>
          -> input values are saved into state
          -> your handler runs -> state changes
          -> UI is re-rendered -> new HTML sent back -> page updates
"""

import html
import inspect
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


# ===============================================================
# 1. ELEMENTS
# ===============================================================
class Element:
    def __init__(self, tag, *children, **props):
        self.tag = tag
        self.children = list(children)
        self.props = props


def Div(*children, **props):
    return Element("div", *children, **props)


def Heading(text, level=1, **props):
    return Element(f"h{level}", text, **props)


def Text(text, **props):
    return Element("p", text, **props)


def Span(*children, **props):
    return Element("span", *children, **props)


def Button(label, **props):
    return Element("button", label, **props)


def Input(**props):
    return Element("input", **props)


def List(*items, **props):
    return Element("ul", *items, **props)


def Item(*children, **props):
    return Element("li", *children, **props)


# ===============================================================
# 2. RENDERER
# ===============================================================
VOID_TAGS = {"input", "br", "hr", "img"}


def render_props(props):
    parts = []
    for key, value in props.items():
        name = key.rstrip("_").replace("_", "-")   # class_ -> class
        if value is None or value is False:
            continue
        if value is True:
            parts.append(name)
        else:
            parts.append(f'{name}="{html.escape(str(value), quote=True)}"')
    return (" " + " ".join(parts)) if parts else ""


def render(node, handlers=None, binds=None):
    """
    Turn an element tree into an HTML string.

    `handlers` is filled with {"e0": function, ...} for every on_click / on_enter.
    `binds` is filled with the names of every Input(bind="name").
    """
    if handlers is None:
        handlers = {}
    if binds is None:
        binds = set()

    if not isinstance(node, Element):
        return html.escape(str(node))

    props = dict(node.props)

    # on_click=function -> data-click="e0"   |   on_enter=function -> data-enter="e1"
    for prop_name, html_name in (("on_click", "data_click"), ("on_enter", "data_enter")):
        function = props.pop(prop_name, None)
        if callable(function):
            event_id = f"e{len(handlers)}"
            handlers[event_id] = function
            props[html_name] = event_id

    # bind="draft" -> data-bind="draft"
    bind = props.pop("bind", None)
    if bind:
        binds.add(bind)
        props["data_bind"] = bind

    attrs = render_props(props)

    if node.tag in VOID_TAGS:
        return f"<{node.tag}{attrs}>"

    inner = "".join(render(child, handlers, binds) for child in node.children)
    return f"<{node.tag}{attrs}>{inner}</{node.tag}>"


# ===============================================================
# 3. STATE
# ===============================================================
class State:
    def __init__(self, **initial):
        self._data = dict(initial)
        self._listeners = []

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        if key in self._data and self._data[key] == value:
            return
        self._data[key] = value
        self._notify()

    def update(self, **changes):
        changed = False
        for key, value in changes.items():
            if key not in self._data or self._data[key] != value:
                self._data[key] = value
                changed = True
        if changed:
            self._notify()

    def subscribe(self, listener):
        self._listeners.append(listener)

    def _notify(self):
        for listener in self._listeners:
            listener()


# ===============================================================
# 4. SERVER (routing + event handling)
# ===============================================================

# Small piece of browser code the framework adds to every page.
# The app developer never writes this. It only:
#   - sends clicks / Enter presses (and the text in bound inputs) to Python
#   - puts the returned HTML on the page
#   - keeps scroll positions and keyboard focus so the page doesn't "jump"
CLIENT_SCRIPT = """
async function send(eventId, source) {
  const values = {};
  document.querySelectorAll("[data-bind]").forEach((input) => {
    values[input.dataset.bind] = input.value;
  });

  const active = document.activeElement;
  const focusKey = source.dataset.focus || (active && active.dataset ? active.dataset.bind : null);

  const scrolls = {};
  document.querySelectorAll("[data-scroll]").forEach((n) => {
    scrolls[n.dataset.scroll] = n.scrollTop;
  });

  const res = await fetch("/event/" + eventId, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(values),
  });
  if (!res.ok) return;
  document.getElementById("root").innerHTML = await res.text();

  document.querySelectorAll("[data-scroll]").forEach((n) => {
    if (n.dataset.scroll in scrolls) n.scrollTop = scrolls[n.dataset.scroll];
  });
  if (focusKey) {
    const input = document.querySelector('[data-bind="' + focusKey + '"]');
    if (input) {
      input.focus();
      try { input.setSelectionRange(input.value.length, input.value.length); } catch (err) {}
    }
  }
}

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-click]");
  if (el) send(el.dataset.click, el);
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Enter") return;
  const el = e.target.closest("[data-enter]");
  if (el) {
    e.preventDefault();
    send(el.dataset.enter, el);
  }
});
"""

DEFAULT_STYLE = """
body { font-family: sans-serif; max-width: 480px; margin: 40px auto; }
button { margin-right: 8px; padding: 6px 14px; font-size: 16px; cursor: pointer; }
input { padding: 6px; font-size: 16px; margin-right: 8px; }
li { margin: 8px 0; }
"""

MAX_BODY = 100_000   # reject request bodies bigger than this (bytes)


def needs_values(handler):
    """True if the handler has a required parameter (so it wants the values)."""
    try:
        params = inspect.signature(handler).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(p.default is p.empty for p in params)


def run_app(build_ui, state=None, host="localhost", port=8000, title="Mini UI", css=None):
    """
    build_ui: function returning the root Element (called on every re-render).
    state:    your State object. Needed if you use Input(bind=...).
    css:      your own stylesheet (a string). If omitted, a simple default is used.
    """
    style = DEFAULT_STYLE if css is None else css
    current = {"handlers": {}, "binds": set()}   # info from the latest render

    def render_ui():
        handlers, binds = {}, set()
        body = render(build_ui(), handlers, binds)
        current["handlers"] = handlers
        current["binds"] = binds
        return body

    class Handler(BaseHTTPRequestHandler):
        # --- GET: send the full page ---
        def do_GET(self):
            if self.path == "/":
                page = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{style}</style>
</head>
<body>
  <div id="root">{render_ui()}</div>
  <script>{CLIENT_SCRIPT}</script>
</body>
</html>"""
                self.send_text(200, page, "text/html")
            else:
                self.send_text(404, "404 - Page not found")

        # --- POST: a button was clicked / Enter was pressed ---
        def do_POST(self):
            if not self.path.startswith("/event/"):
                self.send_text(404, "404 - Page not found")
                return

            # read the (small) JSON body with the input values
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY:
                self.send_text(413, "Request too large")
                return
            try:
                values = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(values, dict):
                    values = {}
            except ValueError:
                values = {}

            # only accept values for inputs that really exist in the UI
            values = {k: str(v) for k, v in values.items() if k in current["binds"]}

            event_id = self.path[len("/event/"):]
            handler = current["handlers"].get(event_id)
            if handler is None:
                self.send_text(404, "Unknown event")
                return

            if state is not None and values:
                state.update(**values)            # 1. typed text -> state

            if needs_values(handler):             # 2. run your function
                handler(values)
            else:
                handler()

            self.send_text(200, render_ui(), "text/html")   # 3. re-render

        def send_text(self, status, text, content_type="text/plain"):
            data = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format, *args):
            pass   # keep the terminal quiet (remove this method to see request logs)

    server = HTTPServer((host, port), Handler)
    print(f"Server running at http://{host}:{port}  (Ctrl + C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
