"""Primary-button canvas border resize, all edges, release, zoom and opt-out.
Run with an isolated plugin: python3 tests/border-resize-nested.py [PLUGIN.so].
"""
import importlib.util, json, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nav", ROOT / "tests/navigator-nested.py")
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS = [("foot", "BorderTest")]
n = nav.Nested(sys.argv[1] if len(sys.argv)>1 else ".build/dev/spatialoverview.so", ".build/shots-border",
    extra=",hover_focus=false,snap_enabled=false,minimap_enabled=false",
    extra_lua="if plugin_loaded then hl.config({plugin={spatialoverview={distortion={enabled=false},navigator={enabled=false},input={button_chord_focus=true}}}}) end")
def check(ok, message):
    assert ok, message
    print("PASS", message, flush=True)
def canvas(action): n.dispatch("hl.plugin.spatialoverview.canvas(" + json.dumps(action) + ")")
def config(value): n.ctl("eval", "hl.config({plugin={spatialoverview={canvas={border_resize=" + value + "}}}})")
def client(): return n.clients()[0]
def geom():
    c=client(); return c["at"] + c["size"]
def screen(): return json.loads(n.ctl("spatialoverview"))["screens"][0]
def box():
    c=client(); s=screen(); z=s["zoom"]; v=s["view"]
    return [(c["at"][0]-v[0])*z,(c["at"][1]-v[1])*z,c["size"][0]*z,c["size"][1]*z]
def mouse(*args):
    subprocess.run([str(ROOT/".build/vpointer"),"1280","720",*map(str,args)],env=n.env(),check=True,timeout=15)
    time.sleep(.15)
def reset():
    n.dispatch('hl.dsp.window.resize({x=360,y=220,window="title:BorderTest"})')
    s=screen(); z=s["zoom"]; v=s["view"]
    x=round(v[0]+(640-180*z)/z); y=round(v[1]+(410-110*z)/z)
    n.dispatch('hl.dsp.window.move({x='+str(x)+',y='+str(y)+',window="title:BorderTest"})')
    time.sleep(.35)
def drag(edge, right=False):
    x,y,w,h=box()
    px=x-3 if "l" in edge else x+w+3 if "r" in edge else x+w/2
    py=y-3 if "t" in edge else y+h+3 if "b" in edge else y+h/2
    dx=-30 if "l" in edge else 30
    dy=-24 if "t" in edge else 24
    mouse("abs",round(px),round(py),"sleep",100,"rdown" if right else "down","sleep",100,
          "rel",dx,dy,"sleep",180,"rel",dx,dy,"sleep",180,"rup" if right else "up","sleep",250)
    return dx*2,dy*2
try:
    subprocess.run(["make","-s","test-tools"],check=True)
    n.launch()
    n.dispatch('hl.plugin.spatialoverview.overview("on all")'); time.sleep(.7)
    canvas("land"); time.sleep(.8)
    reset(); before=geom(); drag("r")
    check(geom()[2:]==before[2:], "border resize defaults off")
    config("true")
    for mode in ("direct", "overview"):
        if mode=="overview":
            n.dispatch('hl.plugin.spatialoverview.overview("toggle all")'); time.sleep(.8)
        for edge in ("l","r","t","b","lt","rt","lb","rb"):
            reset(); before=geom(); z=screen()["zoom"]
            dx,dy=drag(edge); after=geom()
            expected=before[:]
            if "l" in edge: expected[0]+=dx/z; expected[2]-=dx/z
            if "r" in edge: expected[2]+=dx/z
            if "t" in edge: expected[1]+=dy/z; expected[3]-=dy/z
            if "b" in edge: expected[3]+=dy/z
            check(all(abs(a-b)<4 for a,b in zip(after,expected)),f"{mode} {edge}: {before} -> {after}, expected {expected}")
            mouse("rel",20,10)
            check(geom()==after,f"{mode} {edge}: release ends resize")
        reset(); before=geom(); x,y,w,h=box()
        mouse("abs",round(x+w*.5),round(y+h*.6),"down","up")
        check(geom()[2:]==before[2:],f"{mode}: interior click does not resize")
    # Restore the navigator, which owns unmodified right-button gestures.
    n.ctl("eval", "hl.config({plugin={spatialoverview={navigator={enabled=true}}}})")
    if not screen()["navigating"]:
        n.dispatch('hl.plugin.spatialoverview.overview("toggle all")'); time.sleep(.6)
    # Existing right-button resize in navigation mode still works.
    reset(); before=geom(); x,y,w,h=box()
    mouse("abs",round(x+w-30),round(y+h-30),"rdown","rel",40,30,"sleep",180,"rel",40,30,"sleep",180,"rup")
    check(geom()[2]>before[2] and geom()[3]>before[3],"existing right-button resize works")
    config("false"); reset(); before=geom(); drag("r")
    check(geom()[2:]==before[2:],"runtime opt-out stops border resize")
    check(n.proc.poll() is None,"compositor alive")
finally:
    if getattr(n, "log", None):
        n.log.flush()
        Path(".build/border-nested.log").write_text(Path(n.log.name).read_text())
    n.stop()
print("ALL PASSED",flush=True)
