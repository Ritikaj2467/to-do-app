"""
Mini UI Framework - Step 1
Describe a UI as a tree of Python objects and turn it into HTML.

Run:  python step1_mini_ui.py
Then open output.html in your browser.
"""

import html


# ---------------------------------------------------------------
# 1. Element: the building block
# ---------------------------------------------------------------
class Element:
    def __init__(self, tag, *children, **props):
        self.tag = tag                  # e.g. "div", "button"
        self.children = list(children)  # other Elements or plain text
        self.props = props              # e.g. id="main", class_="box"


# ---------------------------------------------------------------
# 2. Helper functions (so we write Div(...) instead of Element("div", ...))
# ---------------------------------------------------------------
def Div(*children, **props):
    return Element("div", *children, **props)


def Heading(text, **props):
    return Element("h1", text, **props)


def Text(text, **props):
    return Element("p", text, **props)


def Button(label, **props):
    return Element("button", label, **props)


def Input(**props):
    return Element("input", **props)


def List(*items, **props):
    return Element("ul", *items, **props)


def Item(*children, **props):
    return Element("li", *children, **props)


# ---------------------------------------------------------------
# 3. Renderer: tree -> HTML string
# ---------------------------------------------------------------
VOID_TAGS = {"input", "br", "hr", "img"}  # tags with no closing tag


def render_props(props):
    parts = []
    for key, value in props.items():
        name = key.rstrip("_").replace("_", "-")  # class_ -> class
        if value is None or value is False:
            continue
        if value is True:
            parts.append(name)  # e.g. disabled
        else:
            parts.append(f'{name}="{html.escape(str(value), quote=True)}"')
    return (" " + " ".join(parts)) if parts else ""


def render(node):
    # plain text or numbers: escape so "<" can't break the page
    if not isinstance(node, Element):
        return html.escape(str(node))

    attrs = render_props(node.props)

    if node.tag in VOID_TAGS:
        return f"<{node.tag}{attrs}>"

    inner = "".join(render(child) for child in node.children)
    return f"<{node.tag}{attrs}>{inner}</{node.tag}>"


# ---------------------------------------------------------------
# 4. Try it out
# ---------------------------------------------------------------
if __name__ == "__main__":
    ui = Div(
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

    body = render(ui)
    print(body)

    page = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Mini UI</title></head>
<body>{body}</body>
</html>"""

    with open("output.html", "w", encoding="utf-8") as f:
        f.write(page)

    print("\nSaved output.html - open it in your browser.")
