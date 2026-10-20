#!/usr/bin/env python3
"""Mission selection lands at 100% with application keyboard focus."""
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nav", ROOT / "tests/navigator-nested.py")
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)
nav.WINDOWS = []
n = nav.Nested(sys.argv[1], ROOT / ".build/shots-mission-activation", extra=",workspace_isolation=true")

def state():
    return json.loads(n.ctl("spatialoverview"))

def action(name):
    n.dispatch("hl.plugin.spatialoverview.canvas(" + json.dumps(name) + ")")
    time.sleep(.7)

def check_landing(title):
    current = state()
    assert not current["mission"]["open"]
    assert all(not s["navigating"] and abs(s["zoom"] - 1) < .001 for s in current["screens"])
    assert n.active()["title"] == title
    n.keys("focus-confirmed")
    print("PASS normal desktop at 100% with application focus: " + title, flush=True)

try:
    n.launch()
    for i in [1, 2]:
        n.dispatch('hl.dsp.focus({workspace="' + str(i) + '"})')
        n.dispatch('hl.dsp.exec_cmd("foot --title=Landing' + str(i) + ' /usr/bin/cat")')
        time.sleep(1)
    n.dispatch('hl.plugin.spatialoverview.overview("on all")')
    time.sleep(.7)
    action("mission")
    window = state()["mission"]["windows"][0]
    monitor = json.loads(n.ctl("monitors", "-j"))[0]
    subprocess.run([str(ROOT / ".build/vpointer"), str(monitor["width"]), str(monitor["height"]),
        "abs", str(round(window["x"] + window["width"] / 2)), str(round(window["y"] + window["height"] / 2)),
        "down", "sleep", "100", "up"], env=n.env(), check=True)
    time.sleep(.8)
    check_landing("Landing1")
    action("mission")
    n.keys("-k", "Right", "-k", "Return")
    time.sleep(.8)
    check_landing("Landing2")
    action("search")
    time.sleep(1)
    before = state()["screens"]
    action("mission")
    n.keys("-k", "Escape")
    time.sleep(.7)
    assert state()["screens"] == before, (before, state()["screens"])
    print("PASS cancel still restores the previous canvas camera", flush=True)
finally:
    n.stop()
