#!/usr/bin/env python3
"""Desktop-only workspace wheel and cursor regression, in a disposable compositor."""
import importlib.util, json, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nav", ROOT / "tests/navigator-nested.py")
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS = []
n = nav.Nested(sys.argv[1], ROOT / ".build/shots-desktop-scroll", extra=",workspace_isolation=true,minimap_enabled=false",
    extra_lua='if plugin_loaded then hl.config({plugin={spatialoverview={distortion={enabled=false}}}}) end\n')
def check(ok, text):
    assert ok, text
    print("PASS", text, flush=True)
def config(enabled):
    n.ctl("eval", "hl.config({plugin={spatialoverview={input={background_workspace_scroll=" + str(enabled).lower() + "}}}})")
def workspace(): return json.loads(n.ctl("activeworkspace", "-j"))["id"]
def ws(i):
    n.dispatch('hl.dsp.focus({workspace="' + str(i) + '"})'); time.sleep(.4)
def mouse(*args):
    m=json.loads(n.ctl("monitors", "-j"))[0]
    subprocess.run([str(ROOT/".build/vpointer"),str(m["width"]),str(m["height"]),*map(str,args)],env=n.env(),check=True,timeout=15)
    time.sleep(.6)
def drag(x=800,y=400,dx=-250,dy=0):
    mouse("abs",x,y,"sleep",100,"down","sleep",80,"rel",dx,dy,"sleep",100,"up")
def wheel(x=800,y=400,direction=1):
    mouse("abs",x,y,"sleep",100,"wheel",direction)
def cursor():
    p=json.loads(n.ctl("cursorpos", "-j")); print("CURSOR",p,flush=True); return (p["x"],p["y"])
app = None
try:
    n.launch(); ws(2)
    wheel(); check(workspace()==2,"disabled by default")
    config(True)
    # Reproduce the user's non-default workspace cursor-warp setting.
    n.ctl("eval", "hl.config({cursor={warp_on_change_workspace=1}})")
    wheel(); check(workspace()==3,"native desktop wheel down advances")
    check(cursor()==(800,400),"native workspace switch preserves cursor")
    wheel(direction=-1); check(workspace()==2,"native desktop wheel up returns")
    check(cursor()==(800,400),"return preserves cursor despite remembered positions")
    drag(); check(workspace()==2,"left drag no longer switches")
    n.dispatch('hl.plugin.spatialoverview.overview("on all")'); time.sleep(.8)
    n.dispatch('hl.plugin.spatialoverview.canvas("land")'); time.sleep(.8)
    n.ctl("eval", "hl.config({cursor={warp_on_change_workspace=1}})")
    wheel(); check(workspace()==3,"persistent desktop wheel down advances")
    check(cursor()==(800,400),"persistent desktop preserves cursor")
    mouse("rel",4,0)
    check(cursor()==(804,400),"first mouse motion does not warp back")
    wheel(direction=-1); check(workspace()==2,"persistent desktop wheel up returns")
    n.dispatch('hl.plugin.spatialoverview.overview("toggle all")'); time.sleep(.8)
    wheel(); check(workspace()==2,"navigator wheel does not switch workspace")
    n.dispatch('hl.plugin.spatialoverview.canvas("land")'); time.sleep(.8)
    n.dispatch('hl.dsp.exec_cmd("foot --app-id=ScrollTest --title=ScrollTest /usr/bin/cat")')
    for _ in range(40):
        if n.clients(): break
        time.sleep(.1)
    time.sleep(.5)
    s=json.loads(n.ctl("spatialoverview"))["screens"][0]; c=n.clients()[0]; z=s["zoom"]; v=s["view"]
    x=round((c["at"][0]+c["size"][0]/2-v[0])*z); y=round((c["at"][1]+c["size"][1]/2-v[1])*z)
    wheel(x,y); check(workspace()==2,"application wheel does not switch")
    app = subprocess.Popen(["qs", "-p", str(ROOT / "tests/layer-popup.qml")], env=n.env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    wheel(700,15); check(workspace()==2,"bar wheel does not switch")
    wheel(180,100); check(workspace()==2,"layer popup wheel does not switch")
    ws(4)
    mouse("abs",800,400,"down","wheel",1,"up")
    check(workspace()==4,"held mouse button prevents wheel switch")
    mouse("abs",800,400,"wheel",1,"sleep",20,"wheel",1,"sleep",20,"wheel",1)
    check(workspace()==5,"wheel burst switches only once during cooldown")
    config(False); wheel(); check(workspace()==5,"runtime disable restores existing behavior")
    check(n.proc.poll() is None,"compositor remains alive")
except Exception:
    log=Path(n.tmp.name)/"hyprland.log"
    if log.exists(): print(log.read_text()[-5000:], flush=True)
    raise
finally:
    if app:
        app.terminate(); app.wait(timeout=5)
    n.stop()
