#!/usr/bin/env python3
"""Mission Control interaction and camera preservation in an isolated compositor."""
import importlib.util, json, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nav", ROOT / "tests/navigator-nested.py")
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS = []
n = nav.Nested(sys.argv[1], ROOT / ".build/shots-mission", extra=",workspace_isolation=true,remember_layout=true",
    extra_lua='hl.config({plugin={spatialoverview={input={mission_control_corner=true}}}})')
def check(ok, msg):
    assert ok, msg
    print("PASS", msg, flush=True)
def state(): return json.loads(n.ctl("spatialoverview"))
def mission(): return state()["mission"]
def camera(): return state()["screens"]
def action(s):
    n.dispatch("hl.plugin.spatialoverview.canvas(" + json.dumps(s) + ")"); time.sleep(.7)
def ws(i):
    n.dispatch('hl.dsp.focus({workspace="' + str(i) + '"})'); time.sleep(.8)
def mouse(*args):
    m = json.loads(n.ctl("monitors", "-j"))[0]
    subprocess.run([str(ROOT/".build/vpointer"),str(m["width"]),str(m["height"]),*map(str,args)],env=n.env(),check=True,timeout=15)
    time.sleep(.7)
def spawn(title):
    n.dispatch("hl.dsp.exec_cmd(" + json.dumps("foot --title=" + title + " /usr/bin/cat") + ")")
    for _ in range(40):
        if any(c["title"] == title for c in n.clients()): break
        time.sleep(.1)
    time.sleep(.5)
try:
    n.launch()
    ws(1); spawn("Mission-One")
    n.dispatch('hl.plugin.spatialoverview.overview("on all")'); time.sleep(.7)
    ws(2); spawn("Mission-Two"); action("search"); action("pan right"); action("land")
    ws(1); mouse("abs",100,100)
    before = camera()
    ownership = {c["title"]:(c["workspace"]["id"],c["at"],c["size"]) for c in n.clients()}
    m=json.loads(n.ctl("monitors","-j"))[0]
    mouse("abs",1,m["height"]-1)
    check(mission()["open"], "bottom-left opens Mission Control")
    windows=mission()["windows"]
    check(len(windows)==2 and {w["workspace"] for w in windows}=={1,2}, "both workspaces contribute live windows")
    two_zoom=windows[0]["zoom"]
    n.shot("two-windows")
    mouse("abs",2,m["height"]-2)
    check(mission()["open"], "staying in corner does not close overlay")
    n.keys("-k","Escape"); time.sleep(.7)
    check(not mission()["open"] and camera()==before, "Escape restores exact previous desktop camera")
    mouse("abs",100,100); mouse("abs",1,m["height"]-1)
    mouse("abs",100,100); mouse("abs",1,m["height"]-1)
    check(not mission()["open"] and camera()==before, "reentering bottom-left cancels and restores camera")
    mouse("abs",100,100); action("mission")
    n.keys("-k","Right")
    check(mission()["selected"]==1, "arrow selects next window without switching workspace")
    check(json.loads(n.ctl("activeworkspace","-j"))["id"]==1, "browsing does not switch workspaces")
    n.keys("-k","Return"); time.sleep(.8)
    check(not mission()["open"] and json.loads(n.ctl("activeworkspace","-j"))["id"]==2, "Enter opens selected window workspace")
    check(not any(c["navigating"] for c in camera()), "selected window opens in normal desktop mode")
    check(n.active()["title"] == "Mission-Two", "selected window receives keyboard focus")
    action("search")
    check(ownership=={c["title"]:(c["workspace"]["id"],c["at"],c["size"]) for c in n.clients()}, "window ownership and geometry stay unchanged")
    n.shot("footer-cards")
    # Footer uses raw coordinates: first card, above the keyboard-help line.
    mouse("abs",m["width"]- (240+24+76) - 300 + 70,m["height"]-110,"down","sleep",100,"up")
    check(json.loads(n.ctl("activeworkspace","-j"))["id"]==1, "footer card switches workspace while staying in canvas")
    check(any(c["navigating"] for c in camera()), "footer switching preserves canvas mode")
    action("land")
    for i in range(3,16):
        ws(i); spawn("Mission-"+str(i))
    ws(1); action("mission")
    windows=mission()["windows"]
    check(len(windows)==15, "all fifteen windows appear across fifteen workspaces")
    check(windows[0]["zoom"] < two_zoom, "fifteen windows use a smaller automatic zoom than two")
    check(all(w["x"]>=0 and w["y"]>=0 and w["x"]+w["width"]<=m["width"] and w["y"]+w["height"]<=m["height"] for w in windows), "all windows fit within screen bounds")
    def overlap(a,b):
        return a["x"] < b["x"]+b["width"] and b["x"] < a["x"]+a["width"] and a["y"] < b["y"]+b["height"] and b["y"] < a["y"]+a["height"]
    check(not any(overlap(a,b) for i,a in enumerate(windows) for b in windows[i+1:]), "window previews do not overlap")
    n.shot("fifteen-windows")
    n.keys("-k","Escape"); time.sleep(.5)
    action("mission"); spawn("Mission-New")
    check(not mission()["open"], "new window dismisses stale overview")
    action("mission"); ws(2)
    check(not mission()["open"], "external workspace switch dismisses overview")
    action("land"); mouse("abs",100,100)
    mouse("abs",100,100,"down","sleep",100,"abs",1,m["height"]-1,"sleep",180,"up")
    check(not mission()["open"], "drag into bottom-left does not activate")
    mouse("abs",100,100); mouse("abs",1,1)
    check(any(c["navigating"] for c in camera()), "top-left canvas toggle still works")
    action("land"); mouse("abs",100,100)
    n.ctl("eval", "hl.config({plugin={spatialoverview={input={mission_control_corner=false}}}})")
    mouse("abs",1,m["height"]-1)
    check(not mission()["open"], "disabled bottom-left option does not activate")
    check(n.proc.poll() is None, "isolated compositor remains healthy")
finally:
    n.stop()
