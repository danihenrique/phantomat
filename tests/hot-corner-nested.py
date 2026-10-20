#!/usr/bin/env python3
"""Hardcoded top-left hot corner regression in an isolated compositor."""
import importlib.util, json, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nav", ROOT / "tests/navigator-nested.py")
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS = []
n = nav.Nested(sys.argv[1], ROOT / ".build/shots-hot-corner")
def check(ok, text):
    assert ok, text
    print("PASS", text, flush=True)
def mouse(*args):
    m = json.loads(n.ctl("monitors", "-j"))[0]
    subprocess.run([str(ROOT/".build/vpointer"), str(m["width"]), str(m["height"]), *map(str,args)], env=n.env(), check=True, timeout=15)
    time.sleep(.6)
def navigating():
    return any(s["navigating"] for s in json.loads(n.ctl("spatialoverview"))["screens"])
def land():
    n.dispatch('hl.plugin.spatialoverview.canvas("land")'); time.sleep(.6)
try:
    n.launch()
    # Keep physical host mouse input out of the virtual-pointer regression.
    hosts = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"]))
    host = next(c for c in hosts if c.get("pid") == n.proc.pid)
    expr = 'hl.dsp.window.move({workspace="special:phantomat-hot-corner-test",follow=false,window="address:' + host["address"] + '"})'
    subprocess.run(["hyprctl", "dispatch", expr], check=True, capture_output=True)
    time.sleep(.4)
    mouse("abs", 100, 100)
    check(not navigating(), "ordinary pointer movement does not open canvas")
    mouse("abs", 1, 1)
    check(navigating(), "top-left opens canvas from native desktop")
    mouse("abs", 2, 2)
    check(navigating(), "movement inside corner does not toggle it closed")
    land()
    mouse("abs", 1, 1)
    check(not navigating(), "landing while inside corner does not immediately reopen")
    mouse("abs", 100, 100)
    mouse("abs", 1, 1)
    check(navigating(), "leaving and reentering opens persistent canvas")
    mouse("abs", 100, 100)
    mouse("abs", 1, 1)
    check(not navigating(), "reentering while navigating exits canvas")
    mouse("abs", 2, 2)
    check(not navigating(), "remaining inside corner after exit does not reopen")
    mouse("abs", 100, 100)
    mouse("abs", 1, 1)
    check(navigating(), "next reentry opens canvas again")
    land()
    mouse("abs", 100, 100, "sleep", 120, "down", "sleep", 100, "abs", 1, 1, "sleep", 100, "up")
    check(not navigating(), "dragging into corner does not activate")
    mouse("abs", 100, 100)
    mouse("abs", 1, 1)
    check(navigating(), "corner rearms after a blocked drag")
    land()
    mouse("abs", 400, 400)
    n.ctl("eval", "hl.config({plugin={spatialoverview={input={background_right_click=true}}}})")
    mouse("abs", 400, 400, "sleep", 100, "rdown", "sleep", 100, "rup")
    check(navigating(), "existing background right-click still opens canvas")
    check(n.proc.poll() is None, "compositor remains alive")
except Exception:
    log = Path(n.tmp.name) / "hyprland.log"
    if log.exists(): print(log.read_text()[-6000:], flush=True)
    raise
finally:
    n.stop()
