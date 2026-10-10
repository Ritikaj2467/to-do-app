"""
Mini UI Framework - Step 3 (part 1)
A State object: holds data, and tells listeners when the data changes.

Run this file directly to test it:  python step3_state.py
"""


class State:
    def __init__(self, **initial):
        self._data = dict(initial)   # the actual data, e.g. {"count": 0}
        self._listeners = []         # functions to call when data changes

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        # do nothing if the value didn't actually change
        if key in self._data and self._data[key] == value:
            return
        self._data[key] = value
        self._notify()

    def update(self, **changes):
        # change several values at once, notify only ONCE
        changed = False
        for key, value in changes.items():
            if key not in self._data or self._data[key] != value:
                self._data[key] = value
                changed = True
        if changed:
            self._notify()

    def subscribe(self, listener):
        # register a function to be called after every change
        self._listeners.append(listener)

    def _notify(self):
        for listener in self._listeners:
            listener()


# ---------------------------------------------------------------
# Quick test (only runs when you run this file directly)
# ---------------------------------------------------------------
if __name__ == "__main__":
    state = State(count=0)
    state.subscribe(lambda: print("UI should re-render! count =", state.get("count")))

    state.set("count", 1)   # changes -> listener runs
    state.set("count", 1)   # same value -> nothing happens
    state.set("count", state.get("count") + 1)
