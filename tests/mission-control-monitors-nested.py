#!/usr/bin/env python3
"""Mission Control restores both monitors and handles output removal."""
import importlib.util, json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nav", ROOT / "tests/navigator-nested.py")
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS = []
n = nav.Nested(sys.argv[1], ROOT / ".build/shots-mission-monitors", extra=",workspace_isolation=true",
    extra_lua='hl.monitor({output="SECOND",mode="1280x720@60",position="1280x0",scale=1})')
def state(): return json.loads(n.ctl("spatialoverview"))
def check(ok,msg):
    assert ok,msg
    print("PASS",msg,flush=True)
def action(s):
    n.dispatch("hl.plugin.spatialoverview.canvas("+json.dumps(s)+")");time.sleep(.5)
try:
    n.launch()
    n.dispatch('hl.dsp.exec_cmd("foot --title=First /usr/bin/cat")');time.sleep(.8)
    n.ctl("output","create","wayland","SECOND");time.sleep(1)
    n.dispatch('hl.plugin.spatialoverview.overview("on all")');time.sleep(.7)
    n.dispatch('hl.dsp.focus({monitor="SECOND"})');time.sleep(.3)
    n.dispatch('hl.dsp.exec_cmd("foot --title=Second /usr/bin/cat")');time.sleep(.8)
    action("land")
    before=state()["screens"]
    check(len(before)==2,"two independent monitor cameras")
    action("mission")
    check(state()["mission"]["open"],"overview opens on second monitor")
    check(len(state()["mission"]["windows"])==2,"overview includes windows belonging to both monitors")
    n.keys("-k","Escape");time.sleep(.5)
    check(state()["screens"]==before,"Escape restores both monitor cameras")
    action("mission")
    n.dispatch('hl.plugin.spatialoverview.overview("toggle all")');time.sleep(.6)
    check(not state()["mission"]["open"] and state()["screens"]==before,"global toggle cancels once without toggling the other monitor")
    action("mission")
    n.ctl("output","remove","SECOND");time.sleep(1)
    check(not state()["mission"]["open"],"removing selector monitor dismisses overlay")
    check(n.proc.poll() is None,"compositor survives monitor removal")
finally:
    n.stop()
