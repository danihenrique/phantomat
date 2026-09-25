"""Both-button focusing with real pointer events and app-side click logging."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('nav', ROOT/'tests/navigator-nested.py')
nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
nav.WINDOWS=[('foot','Other')]
n=nav.Nested(str(ROOT/'spatialoverview.so'),str(ROOT/'.build/chord-shots'),extra=',groups=true,hover_focus=false,snap_enabled=false',
    extra_lua='\nif plugin_loaded then hl.config({plugin={spatialoverview={distortion={enabled=false}}}}) end\n')
def canvas(action):n.dispatch('hl.plugin.spatialoverview.canvas('+json.dumps(action)+')')
def state():return json.loads(n.ctl('spatialoverview'))
def screen():return state()['screens'][0]
def client(title):return next(c for c in n.clients() if c['title']==title)
def config(expr):n.ctl('eval','hl.config({plugin={spatialoverview={'+expr+'}}})')
def check(ok,text):
    assert ok,text
    print('PASS',text,flush=True)
def mouse(*args):
    m=json.loads(n.ctl('monitors','-j'))[0]
    subprocess.run([str(ROOT/'.build/vpointer'),str(m['width']),str(m['height']),*map(str,args)],env=n.env(),check=True,timeout=10)
    time.sleep(.4)
def point():
    c=client('ButtonLog');s=screen();v=s['view'];z=s['zoom']
    return round((c['at'][0]+c['size'][0]*.5-v[0])*z),round((c['at'][1]+c['size'][1]*.6-v[1])*z)
def events():return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
def clear():log.write_text('')
def offset():
    c=client('ButtonLog')
    n.dispatch('hl.dsp.window.move({x='+str(c['at'][0]+70)+',y='+str(c['at'][1]+40)+',window="title:ButtonLog"})')
    time.sleep(.5)
def chord(right_first=False,delay=35):
    first,second=('rdown','down') if right_first else ('down','rdown')
    releases=('rup','up') if right_first else ('up','rup')
    mouse('abs',*point(),first,'sleep',delay,second,'sleep',80,releases[0],'sleep',30,releases[1])
    time.sleep(.7)
app=None
try:
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','gtk4'],text=True).split()
    subprocess.run(['cc',str(ROOT/'tests/tools/button-log.c'),'-o',str(ROOT/'.build/button-log'),*flags],check=True)
    n.launch();log=Path(n.tmp.name)/'buttons.jsonl'
    app=subprocess.Popen([str(ROOT/'.build/button-log'),str(log)],env=n.env(),stdout=subprocess.DEVNULL,stderr=open(Path(n.tmp.name)/'app.log','w'))
    for _ in range(60):
        if any(c['title']=='ButtonLog' for c in n.clients()):break
        time.sleep(.1)
    check(any(c['title']=='ButtonLog' for c in n.clients()),'button logger mapped')
    n.dispatch('hl.plugin.spatialoverview.overview("on all")');time.sleep(.7)
    canvas('search ButtonLog');n.keys('-k','Return');time.sleep(1)
    offset();before=screen()['view'];clear();chord()
    check(screen()['view']==before,'button chord disabled by default')
    check(len(events())==4,'disabled chord forwards both native clicks')
    config('input={button_chord_focus=true,button_chord_timeout=120,ctrl_click_focus=true,background_right_click=true}')
    for right_first in (False,True):
        canvas('search ButtonLog');n.keys('-k','Return');time.sleep(.8);offset();clear()
        before=client('ButtonLog')['at'][:];chord(right_first)
        c=client('ButtonLog');s=screen()
        check(not s['navigating'] and n.active()['title']=='ButtonLog','chord focuses without opening overview, right-first='+str(right_first))
        check(abs(c['at'][0]+c['size'][0]/2-s['view'][0]-s['view'][2]/2)<5,'chord centers window')
        check(c['at']==before,'chord does not reposition window')
        check(not events(),'neither chord click reaches app')
    for down,up,button in (('down','up',1),('rdown','rup',3)):
        clear();mouse('abs',*point(),down,'sleep',35,up)
        check(events()==[{'button':button,'pressed':True},{'button':button,'pressed':False}],'short ordinary click delivered once: '+str(button))
    clear();mouse('abs',*point(),'down','sleep',250,'up')
    check(events()==[{'button':1,'pressed':True},{'button':1,'pressed':False}],'timeout delivers normal held click')
    clear();before=screen()['view'];chord(delay=250)
    check(len(events())==4 and screen()['view']==before,'slow second press remains native input')
    clear();mouse('abs',*point(),'down','rel',35,0,'sleep',50,'up')
    check(events()==[{'button':1,'pressed':True},{'button':1,'pressed':False}],'ordinary drag forwards a balanced button pair')
    # Build a group and move one member: framing must use the whole group.
    for title in ('ButtonLog','Other'):
        n.dispatch('hl.dsp.focus({window="title:'+title+'"})');canvas('select')
    canvas('group');canvas('search ButtonLog');n.keys('-k','Return');time.sleep(1)
    offset();clear();chord(True)
    a,b=client('ButtonLog'),client('Other');s=screen();v=s['view']
    cx=(min(a['at'][0],b['at'][0])+max(a['at'][0]+a['size'][0],b['at'][0]+b['size'][0]))/2
    check(abs(cx-v[0]-v[2]/2)<5 and len(state()['groups'][0])==2,'chord frames the whole group')
    check(not events(),'group chord does not leak clicks')
    # The original selection shortcut still works in overview.
    canvas('search');canvas('clear-selection');time.sleep(.7)
    held=subprocess.Popen(['wtype','-M','ctrl','-s','1100','-m','ctrl'],env=n.env());time.sleep(.25)
    mouse('abs',*point(),'down','up');held.wait(timeout=5)
    check('ButtonLog' in state()['selection'],'Ctrl-click selection remains available in overview')
    mouse('abs',3,3,'rdown','rup');time.sleep(.8)
    check(not screen()['navigating'],'background right-click still exits with chord enabled')
    mouse('abs',300,3,'rdown','sleep',600,'rel',-90,0,'sleep',150,'rup');time.sleep(.8)
    check(screen()['navigating'],'background right-hold still opens and navigates with chord enabled')
    after=screen()['view'];mouse('rel',30,0)
    check(screen()['view']==after,'background release is not trapped by chord detection')
    check(not n.ctl('configerrors'),'configuration valid')
    print('ALL PASSED',flush=True)
except Exception:
    if 'log' in globals():print('APP EVENTS',events(),flush=True)
    app_log=Path(n.tmp.name)/'app.log'
    if app_log.exists():print(app_log.read_text(),flush=True)
    print('STATE',state(), 'POINT',point(),flush=True)
    raise
finally:
    if app and app.poll() is None:app.terminate();app.wait(timeout=5)
    n.stop()
