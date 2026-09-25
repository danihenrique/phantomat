"""Opt-in background click, focus-only click and spatial groups in isolation.
No user config changes; real virtual-pointer events exercise press/release,
Ctrl-click selection, group drag and Shift-drag adjustment.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('nav', ROOT/'tests/navigator-nested.py')
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS = [('foot', 'GroupA'), ('foot', 'GroupB'), ('foot', 'GroupC')]
n = nav.Nested(str(ROOT/'spatialoverview.so'), str(ROOT/'.build/shots-interactions'), extra=',hover_focus=false,snap_enabled=false',
    extra_lua='\nif plugin_loaded then hl.config({plugin={spatialoverview={distortion={enabled=false},chrome_animation={enabled=false}}}}) end\n')

def state(): return json.loads(n.ctl('spatialoverview'))
def screen(): return state()['screens'][0]
def client(title): return next(c for c in n.clients() if c['title'] == title)
def canvas(action): n.dispatch('hl.plugin.spatialoverview.canvas(' + json.dumps(action) + ')')
def config(expr): n.ctl('eval', 'hl.config({plugin={spatialoverview={' + expr + '}}})')
def check(ok, text):
    assert ok, text
    print('PASS', text, flush=True)
def mouse(*args):
    info = json.loads(n.ctl('monitors','-j'))[0]
    subprocess.run([str(ROOT/'.build/vpointer'),str(info['width']),str(info['height']),*map(str,args)],env=n.env(),check=True,timeout=15)
    time.sleep(.3)
def point(title):
    c=client(title); s=screen(); v=s['view']; z=s['zoom']
    return round((c['at'][0]+c['size'][0]*.5-v[0])*z),round((c['at'][1]+c['size'][1]*.65-v[1])*z)
def click(title,modifier=None,right=False):
    p=None
    if modifier:
        p=subprocess.Popen(['wtype','-M',modifier,'-s','1100','-m',modifier],env=n.env())
        time.sleep(.25)
    mouse('abs',*point(title),'sleep',100,'rdown' if right else 'down','sleep',80,'rup' if right else 'up')
    if p: p.wait(timeout=5)
    time.sleep(.5)
def focus(title):
    n.dispatch('hl.dsp.focus({window="title:' + title + '"})')
    time.sleep(.3)
def move(title,x,y):
    n.dispatch('hl.dsp.window.move({x='+str(round(x))+',y='+str(round(y))+',window="title:'+title+'"})')
def drag(title,modifier=None):
    p=None
    if modifier:
        p=subprocess.Popen(['wtype','-M',modifier,'-s','1800','-m',modifier],env=n.env()); time.sleep(.25)
    mouse('abs',*point(title),'sleep',120,'down','sleep',80,'rel',30,15,'sleep',150,'rel',40,15,'sleep',150,'up','sleep',200)
    if p: p.wait(timeout=5)
    time.sleep(.7)

try:
    n.launch()
    # Both options default off: a native background click does nothing.
    mouse('abs',3,3,'rdown','rup')
    check(not state()['screens'], 'background click disabled by default')
    config('input={background_right_click=true}')
    # The desktop shortcut must not steal clicks on layer-shell panels.
    env=n.env(); env['LD_PRELOAD']='/usr/lib/libgtk4-layer-shell.so'
    mon=json.loads(n.ctl('monitors','-j'))[0]
    bar=subprocess.Popen(['python3',str(ROOT/'tests/tools/layer-bar.py'),mon['name']],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            if 'test-bar' in n.ctl('layers'): break
            time.sleep(.1)
        check('test-bar' in n.ctl('layers'), 'test panel mapped')
        mouse('abs',round(mon['width']/2),10,'rdown','rup')
        check(not state()['screens'], 'right click on panel is not a desktop click')
    finally:
        bar.terminate(); bar.wait(timeout=5)
    time.sleep(.5)
    c=client('GroupA')
    mouse('abs',c['at'][0]+50,c['at'][1]+50,'rdown','rup')
    check(not state()['screens'], 'right click on native app does not open canvas')
    mouse('abs',3,3,'rdown','rup')
    time.sleep(1.2)
    check(screen()['navigating'], 'native background click opens overview')
    # Arrange deterministic hit targets, clear of the HUD.
    info=json.loads(n.ctl('monitors','-j'))[0]; W=info['width']; H=info['height']
    for i,title in enumerate(('GroupA','GroupB','GroupC')):
        n.dispatch('hl.dsp.window.resize({x=180,y=120,window="title:'+title+'"})')
        move(title,W*(.1+i*.35),H*.7)
    canvas('viewport 0 0'); time.sleep(1)
    click('GroupA'); time.sleep(1)
    check(not screen()['navigating'], 'default primary click still lands')
    # Right click in an app must remain app input at 100%.
    click('GroupA',right=True)
    check(not screen()['navigating'], 'right click inside canvas app stays native')
    mouse('abs',3,3,'rdown','rup'); time.sleep(1)
    check(screen()['navigating'], 'background click reopens persistent canvas')
    config('navigator={click_to_focus=true},canvas={groups=true}')
    canvas('viewport 0 0'); time.sleep(.8)
    before=screen()
    click('GroupB')
    check(n.active()['title']=='GroupB' and screen()['navigating'], 'focus-only click activates window and keeps overview')
    check(screen()['view']==before['view'] and screen()['zoom']==before['zoom'], 'focus-only click does not move camera')
    click('GroupA','ctrl'); click('GroupB','ctrl')
    check(set(state()['selection'])=={'GroupA','GroupB'}, 'Ctrl-click selects two windows')
    click('GroupB','ctrl'); check(state()['selection']==['GroupA'], 'Ctrl-click deselects')
    click('GroupB','ctrl')
    # Move the second selected app far away; grouping must bring it back.
    move('GroupB',5000,4000); time.sleep(1)
    sizes={t:client(t)['size'] for t in ('GroupA','GroupB')}
    n.keys('-M','ctrl','g','-m','ctrl'); time.sleep(1)
    check(len(state()['groups'])==1 and len(state()['groups'][0])==2, 'Ctrl+G creates a spatial group')
    check(all(client(t)['size']==sizes[t] for t in sizes), 'grouping preserves window sizes')
    a,b=client('GroupA'),client('GroupB')
    check(abs(a['at'][0]-b['at'][0])<500 and abs(a['at'][1]-b['at'][1])<500, 'distant windows are brought together')
    before={t:client(t)['at'][:] for t in sizes}
    drag('GroupA')
    delta={t:[client(t)['at'][i]-before[t][i] for i in (0,1)] for t in sizes}
    check(delta['GroupA']==delta['GroupB'] and abs(delta['GroupA'][0])>20, 'drag moves the whole group by the same offset')
    canvas('undo'); time.sleep(1)
    check(all(client(t)['at']==before[t] for t in sizes), 'undo restores every dragged group member')
    canvas('redo'); time.sleep(1)
    check(all(client(t)['at']==[before[t][i]+delta[t][i] for i in (0,1)] for t in sizes), 'redo restores group movement')
    before_b=client('GroupB')['at'][:]; before_a=client('GroupA')['at'][:]
    drag('GroupA','shift')
    check(client('GroupB')['at']==before_b and client('GroupA')['at']!=before_a, 'Shift-drag adjusts one member only')
    # Individual resizing does not dissolve membership or resize other members.
    n.dispatch('hl.dsp.window.resize({x=220,y=150,window="title:GroupA"})'); time.sleep(.8)
    check(client('GroupB')['size']==sizes['GroupB'] and len(state()['groups'])==1, 'members can resize independently')
    canvas('search GroupA'); n.keys('-k','Return'); time.sleep(1)
    s=screen(); v=s['view']
    boxes=[client(t) for t in sizes]
    cx=(min(c['at'][0] for c in boxes)+max(c['at'][0]+c['size'][0] for c in boxes))/2
    cy=(min(c['at'][1] for c in boxes)+max(c['at'][1]+c['size'][1] for c in boxes))/2
    check(abs(cx-(v[0]+v[2]/2))<5 and abs(cy-(v[1]+v[3]/2))<5, 'landing centers group bounds rather than one member')
    n.dispatch('hl.dsp.window.fullscreen({mode="fullscreen"})'); time.sleep(1.2)
    check(len(state()['groups'])==1, 'fullscreen preserves spatial group membership')
    n.dispatch('hl.dsp.window.fullscreen({mode="fullscreen"})'); time.sleep(1.2)
    check(len(state()['groups'])==1, 'leaving fullscreen keeps group usable')
    n.dispatch('hl.plugin.spatialoverview.overview("off all")'); time.sleep(1.5)
    check(len(state()['groups'])==1, 'closing canvas preserves spatial associations')
    n.dispatch('hl.plugin.spatialoverview.overview("toggle all")'); time.sleep(1.5)
    check(len(state()['groups'])==1, 'reopening canvas restores usable groups')
    canvas('search GroupA'); time.sleep(.5)
    n.keys('-M','ctrl','-M','shift','g','-m','shift','-m','ctrl')
    check(not state()['groups'], 'Ctrl+Shift+G dissolves group')
    # Recreate then close a member: no stale group or dangling reference.
    for t in ('GroupA','GroupB'):
        focus(t); canvas('select')
    canvas('group')
    n.dispatch('hl.dsp.window.close({window="title:GroupB"})'); time.sleep(.8)
    check(not state()['groups'], 'closing member prunes single-window group')
    check(not n.ctl('configerrors'), 'configuration remains valid')
    print('ALL PASSED',flush=True)
except Exception:
    if getattr(n,'log',None):
        n.log.flush(); print(Path(n.log.name).read_text()[-2000:],flush=True)
    print('STATE',state(),flush=True)
    raise
finally:
    n.stop()
