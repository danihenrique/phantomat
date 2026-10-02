#!/usr/bin/env python3
"""Independent native workspaces: render, pointer, focus, camera and moves.
Run only inside the disposable compositor created by this harness.
WORKSPACE_BASELINE=1 exercises the old shared mode to reproduce the failure.
"""
import importlib.util, json, os, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nav", ROOT / "tests/navigator-nested.py")
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS = []
baseline = os.environ.get("WORKSPACE_BASELINE") == "1"
n = nav.Nested(sys.argv[1] if len(sys.argv)>1 else ".build/workspaces/spatialoverview.so", ROOT/".build/shots-workspaces",
    extra=("" if baseline else ",workspace_isolation=true") + ",hover_focus=true,snap_enabled=false,minimap_enabled=false,remember_layout=true",
    extra_lua='if plugin_loaded then hl.config({input={resolve_binds_by_sym=true},plugin={spatialoverview={distortion={enabled=false}}}}) end\n'
      + 'function workspaceTestSwitch(num) if not pcall(hl.plugin.spatialoverview._dispatch,"canvas","go " .. num) then hl.dispatch(hl.dsp.focus({workspace=tostring(num)})) end end\n'
      + 'hl.bind("SUPER + 1", function() workspaceTestSwitch(1) end)\n'
      + 'hl.bind("SUPER + 2", function() workspaceTestSwitch(2) end)\n')

def check(ok, message):
    assert ok, message
    print("PASS", message, flush=True)
def canvas(action):
    n.dispatch("hl.plugin.spatialoverview.canvas(" + json.dumps(action) + ")"); time.sleep(1.4)
def ws(num):
    n.dispatch('hl.dsp.focus({workspace="' + str(num) + '"})'); time.sleep(.8)
def screen(): return json.loads(n.ctl("spatialoverview"))["screens"][0]
def cam():
    s=screen(); m=next(m for m in json.loads(n.ctl("monitors","-j")) if m["name"]==s["monitor"])
    v=s["view"]
    # The nested output can be resized by the parent during a config reload.
    # Compare the camera offset, not the viewport dimensions.
    offset=[round(v[0]+v[2]/2-m["x"]-m["width"]/m["scale"]/2),
            round(v[1]+v[3]/2-m["y"]-m["height"]/m["scale"]/2)]
    return (s["zoom"], offset, s["navigating"])
def client(title): return next(c for c in n.clients() if c["title"]==title)
def mouse(*args):
    subprocess.run([str(ROOT/".build/vpointer"),"1280","720",*map(str,args)],env=n.env(),check=True,timeout=15); time.sleep(.2)
def pixels(rgb):
    raw=subprocess.run(["grim","-t","ppm","-"],env=n.env(),capture_output=True,check=True,timeout=10).stdout
    data=raw.split(b"\n",3)[3]
    return sum(all(abs(data[i+j]-rgb[j])<12 for j in range(3)) for i in range(0,len(data)-2,12))
def spawn(title, color):
    n.dispatch("hl.dsp.exec_cmd("+json.dumps(f"foot --app-id={title} --title={title} --override=colors-dark.background={color} /usr/bin/cat")+")")
    for _ in range(40):
        if any(c["title"]==title for c in n.clients()): break
        time.sleep(.1)
    time.sleep(.4)
def place(title):
    s=screen(); z=s["zoom"]; v=s["view"]
    n.dispatch('hl.dsp.window.resize({x=400,y=260,window="title:'+title+'"})')
    n.dispatch('hl.dsp.window.move({x='+str(round(v[0]+360/z))+',y='+str(round(v[1]+300/z))+',window="title:'+title+'"})'); time.sleep(.5)
try:
    subprocess.run(["make","-s","test-tools"],check=True)
    n.launch(); ws(1); spawn("WorkspaceRed", "b02020")
    n.dispatch('hl.plugin.spatialoverview.overview("on all")'); time.sleep(.8)
    place("WorkspaceRed")
    n.shot("initial-workspace-1")
    check(pixels((176,32,32))>1000, "workspace 1 window actually rendered")
    before=client("WorkspaceRed")["at"]
    camera1=cam()
    ws(2)
    n.shot("empty-workspace-2")
    check(pixels((176,32,32))<20, "workspace 1 has zero rendered content on empty workspace 2")
    check(client("WorkspaceRed")["workspace"]["id"]==1, "switch does not migrate workspace 1 windows")
    mouse("abs",500,400,"down","up")
    n.keys("sentinel")
    check(n.active().get("title")!="WorkspaceRed", "click and keyboard cannot focus invisible workspace 1 window")
    check(client("WorkspaceRed")["workspace"]["id"]==1, "click does not pull hidden window into workspace 2")
    spawn("WorkspaceBlue", "2040b0"); place("WorkspaceBlue")
    check(pixels((32,64,176))>1000 and pixels((176,32,32))<20, "only workspace 2 window renders")
    canvas("zoom out"); canvas("pan right")
    camera2=cam()
    ws(1)
    check(cam()==camera1, f"workspace 1 camera restored exactly: {cam()} == {camera1}")
    check(client("WorkspaceRed")["at"]==before, "workspace 1 geometry unchanged")
    check(pixels((32,64,176))<20 and pixels((176,32,32))>1000, "return hides workspace 2 and shows workspace 1")
    # Replay the registered keybinding callback; wtype's synthesized keymap
    # does not reliably activate compositor shortcuts in nested sessions.
    n.ctl("eval", "workspaceTestSwitch(2)"); time.sleep(.8)
    check(cam()==camera2, f"workspace key uses native switch and restores workspace 2 zoom and pan: {cam()} vs {camera2}; active {n.ctl('activeworkspace')}")
    canvas("search WorkspaceRed")
    check(json.loads(n.ctl("spatialoverview"))["selected"]=="", "search results exclude the other workspace")
    canvas("land"); time.sleep(.5)
    check(n.active().get("title")!="WorkspaceRed", "navigator cannot select windows on another workspace")
    ws(1)
    n.dispatch('hl.dsp.focus({window="title:WorkspaceRed"})'); time.sleep(.3)
    n.dispatch('hl.dsp.window.move({workspace="2",follow=false})'); time.sleep(.8)
    check(client("WorkspaceRed")["workspace"]["id"]==2, "native silent move changes workspace ownership")
    check(pixels((176,32,32))<20, "moved window disappears immediately from source canvas")
    ws(2)
    check(client("WorkspaceRed")["workspace"]["id"]==2, "destination keeps ownership after switch")
    # Undo belongs to the current workspace and must not retrieve a moved window.
    ws(1); spawn("WorkspaceGreen", "208040"); place("WorkspaceGreen")
    canvas("nudge right")
    red_before=client("WorkspaceRed")["at"]
    ws(2); n.dispatch('hl.dsp.focus({window="title:WorkspaceBlue"})'); time.sleep(.3)
    blue_before=client("WorkspaceBlue")["at"]
    canvas("nudge left")
    ws(1); canvas("undo")
    check(client("WorkspaceRed")["at"]==red_before, "undo in workspace 1 does not change workspace 2 geometry")
    check(client("WorkspaceBlue")["at"]!=blue_before, "workspace 1 undo does not undo workspace 2 edit")
    ws(2); canvas("undo")
    check(client("WorkspaceBlue")["at"]==blue_before, "workspace 2 has its own undo journal")

    # Native X11 applications use the same render/input boundary.
    ws(3)
    fifo=Path(n.tmp.name)/"game.in"; os.mkfifo(fifo)
    game_in=os.open(fifo,os.O_RDWR)
    n.dispatch("hl.dsp.exec_cmd("+json.dumps(f"sh -c '{ROOT}/.build/x11-game WorkspaceX11 < {fifo}'")+")")
    for _ in range(40):
        if any(c["title"]=="WorkspaceX11" for c in n.clients()): break
        time.sleep(.15)
    place("WorkspaceX11")
    check(pixels((42,90,8))>1000, "X11 window rendered on its workspace")
    ws(4)
    check(pixels((42,90,8))<20, "X11 window absent from another workspace")
    mouse("abs",500,400,"down","up")
    check(n.active().get("title")!="WorkspaceX11", "hidden X11 window cannot receive pointer focus")
    ws(3)
    check(pixels((42,90,8))>1000, "X11 window restored on return")
    os.close(game_in)

    # Save all workspace cameras, actually unload/reload, then revisit both.
    ws(1); saved1=cam()
    ws(2); saved2=cam()
    ownership={c["title"]:c["workspace"]["id"] for c in n.clients()}
    geometry={c["title"]:(c["at"],c["size"]) for c in n.clients()}
    canvas("save-memory")
    n.ctl("plugin","unload",str(n.plugin)); time.sleep(.4)
    check({c["title"]:c["workspace"]["id"] for c in n.clients()}==ownership, "unload preserves explicitly moved workspace membership")
    n.ctl("plugin","load",str(n.plugin)); n.ctl("reload"); time.sleep(.4)
    n.dispatch('hl.plugin.spatialoverview.overview("on all")'); time.sleep(.8)
    ws(1); check(cam()==saved1, f"workspace 1 camera survives plugin reload: {cam()} vs {saved1}")
    ws(2); check(cam()==saved2, f"workspace 2 camera survives plugin reload: {cam()} vs {saved2}")
    check(all((c["at"],c["size"])==geometry[c["title"]] for c in n.clients() if c["workspace"]["id"] in (1,2)), "both workspace layouts survive plugin reload")
    check(n.proc.poll() is None, "compositor alive")
    n.shot("workspace-2-result")
finally:
    n.stop()
print("ALL PASSED")
