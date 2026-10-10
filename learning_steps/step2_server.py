"""
Mini UI Framework - Step 2
Serve the UI in a browser using Python's built-in http.server.

Keep this file in the SAME folder as step1_mini_ui.py.

Run:  python step2_server.py
Then open http://localhost:8000 in your browser.
Stop the server with Ctrl + C.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer

from step1_mini_ui import Div, Heading, Text, Button, Input, List, Item, render


# ---------------------------------------------------------------
# 1. Your UI lives in a function.
#    The server calls it every time the page is requested.
#    (In Step 3 this will read from state, so the page can change.)
# ---------------------------------------------------------------
def build_ui():
    return Div(
        Heading("My First UI"),
        Text("Count: 0"),
        Button("+1", id="inc"),
        Input(type="text", placeholder="Type here"),
        List(
            Item("Learn Python"),
            Item("Build a framework"),
        ),
        class_="app",
    )


# ---------------------------------------------------------------
# 2. Wrap the rendered UI in a full HTML page
# ---------------------------------------------------------------
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
# 3. The request handler: decides what to send back for each request
# ---------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            page = build_page().encode("utf-8")   # text -> bytes
            self.send_response(200)                # 200 = OK
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)                 # send the page
        else:
            self.send_response(404)                # 404 = not found
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 - Page not found")


# ---------------------------------------------------------------
# 4. Start the server
# ---------------------------------------------------------------
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
