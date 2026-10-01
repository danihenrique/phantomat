"""Closing a temporary fullscreen window restores a grouped canvas view.
Runs only in a disposable compositor with isolated state.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nav", ROOT / "tests/navigator-nested.py")
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)
nav.WINDOWS = [("foot", "GroupA"), ("foot", "GroupB")]
n = nav.Nested(sys.argv[1] if len(sys.argv) > 1 else ROOT / ".build/dev/spatialoverview.so",
               ROOT / ".build/shots-fullscreen-groups",
               extra=",groups=true,remember_layout=true,hover_focus=false,snap_enabled=false")
app = None

def state():
    return json.loads(n.ctl("spatialoverview"))

def canvas(action):
    n.dispatch("hl.plugin.spatialoverview.canvas(" + json.dumps(action) + ")")

try:
    n.launch()
    n.dispatch('hl.plugin.spatialoverview.overview("on all")')
    time.sleep(1)
    members = n.clients()
    for c in members:
        n.dispatch('hl.dsp.focus({window="address:' + c["address"] + '"})')
        canvas("select")
    canvas("group")
    canvas("search GroupA")
    n.keys("-k", "Return")
    time.sleep(1)
    groups = state()["groups"]
    assert any(set(g) == {"GroupA", "GroupB"} for g in groups), "group not created"
    positions = {c["address"]: (c["at"], c["size"]) for c in n.clients()}
    for app_id in ("temporary-fullscreen", "org.omarchy.screensaver"):
        app = subprocess.Popen(["foot", "--app-id=" + app_id, "--title=Ephemeral", "/usr/bin/cat"],
                               env=n.env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            ephemeral = next((c for c in n.clients() if c["title"] == "Ephemeral"), None)
            if ephemeral:
                break
            time.sleep(.1)
        assert ephemeral, "temporary window did not map"
        n.dispatch('hl.dsp.focus({window="address:' + ephemeral["address"] + '"})')
        n.dispatch('hl.dsp.window.fullscreen({mode="fullscreen"})')
        time.sleep(1)
        assert state()["fullscreen"], "temporary window did not enter fullscreen"
        app.terminate()
        app.wait(timeout=5)
        app = None
        time.sleep(1.5)
        restored = state()
        assert not restored["fullscreen"], "fullscreen state remained after window exit"
        assert sorted(map(sorted, restored["groups"])) == sorted(map(sorted, groups)), "groups changed"
        assert {c["address"]: (c["at"], c["size"]) for c in n.clients()} == positions, "group geometry changed"
        active = n.active()
        assert active.get("title") in ("GroupA", "GroupB"), "focus not restored to surviving group"
        x, y, w, h = restored["screens"][0]["view"]
        cx, cy = active["at"]
        cw, ch = active["size"]
        assert cx < x + w and cx + cw > x and cy < y + h and cy + ch > y, "restored view misses active window"
        assert not n.ctl("configerrors"), "configuration errors after fullscreen exit"
        print("PASS fullscreen exit restores focus/view and preserves group geometry: " + app_id, flush=True)
finally:
    if app and app.poll() is None:
        app.terminate()
        app.wait(timeout=5)
    n.stop()
