"""Persistence through real plugin unload/reload and a new compositor session.
Uses isolated XDG_STATE_HOME; never writes the user's config or saved layout.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('nav', ROOT/'tests/navigator-nested.py')
nav=importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS=[('foot','PersistA'),('foot','PersistB'),('foot','Twin'),('foot','Twin')]
state_dir=tempfile.TemporaryDirectory(prefix='phantomat-persistence-')

def launch(plugin=None):
    n=nav.Nested(plugin or str(ROOT/'spatialoverview.so'),str(ROOT/'.build/persistence-shots'),state=state_dir.name,
        extra=',remember_layout=true,groups=true,hover_focus=false,snap_enabled=false',
        extra_lua='\nif plugin_loaded then hl.config({plugin={spatialoverview={distortion={enabled=false}}}}) end\n')
    n.launch()
    assert len(n.clients())==len(nav.WINDOWS), 'test windows did not map'
    n.dispatch('hl.plugin.spatialoverview.overview("on all")'); time.sleep(1)
    return n

def canvas(action): n.dispatch('hl.plugin.spatialoverview.canvas('+json.dumps(action)+')')
def state(): return json.loads(n.ctl('spatialoverview'))
def screen(): return state()['screens'][0]
def check(ok,text):
    assert ok,text
    print('PASS',text,flush=True)
def focus(c): n.dispatch('hl.dsp.focus({window="address:'+c['address']+'"})')
def geometry(): return {c['address']:(c['at'],c['size']) for c in n.clients()}
def file_entries():
    lines=(Path(state_dir.name)/'spatial-overview/canvas-memory.tsv').read_text().splitlines()
    return [line.split('\t') for line in lines if line.startswith('window\t')]
def unload(save=True):
    env=n.env();env['HYPRLAND_INSTANCE_SIGNATURE']=n.sig;env['XDG_STATE_HOME']=state_dir.name
    script='project_dir='+str(ROOT)+'\nsource scripts/common.sh\n'+('remember_canvas_layout\n' if save else '')+'safe_unload\n'
    subprocess.run(['bash','-e','-c',script],cwd=ROOT,env=env,check=True,timeout=40)
def reload():
    n.ctl('plugin','load',str(ROOT/'spatialoverview.so')); n.ctl('reload'); time.sleep(.4)
    n.dispatch('hl.plugin.spatialoverview.overview("on all")'); time.sleep(1.3)

n=None
try:
    n=launch(os.environ.get('PHANTOMAT_TEST_OLD_PLUGIN'))
    clients=n.clients(); a=next(c for c in clients if c['title']=='PersistA'); b=next(c for c in clients if c['title']=='PersistB')
    twins=[c for c in clients if c['title']=='Twin']
    for group in ((a,b),twins):
        for c in group: focus(c);canvas('select')
        canvas('group')
    # Custom geometry deliberately differs from compact group layout.
    for i,c in enumerate(clients):
        n.dispatch('hl.dsp.window.resize({x='+str(310+30*i)+',y='+str(210+20*i)+',window="address:'+c['address']+'"})')
        n.dispatch('hl.dsp.window.move({x='+str(-1300+430*i)+',y='+str(200+290*i)+',window="address:'+c['address']+'"})')
    time.sleep(1)
    canvas('search PersistA');n.keys('-k','Return');time.sleep(1)
    canvas('search');canvas('pan right');time.sleep(1)
    expected=geometry();before=screen();groups=state()['groups']
    old_build=state().get('memory_version',0)<2
    if not old_build: canvas('save-memory')
    unload()
    entries=file_entries()
    check(all(any(int(e[8])==int(c['stableId'],16) for e in entries) for c in clients),'file stores compositor stable IDs')
    check(len({e[9] for e in entries if e[9]!='0'})==2,'file stores both groups')
    reload()
    check(geometry()==expected,'reload preserves exact positions and sizes including identical titles')
    check(sorted(map(sorted,state()['groups']))==sorted(map(sorted,groups)),'reload preserves groups without repacking')
    after=screen()
    check(after['navigating']==before['navigating'] and abs(after['zoom']-before['zoom'])<.001 and
          all(abs(x-y)<1 for x,y in zip(after['view'],before['view'])),'reload preserves camera, zoom and canvas mode')
    # Flush at unload must catch a just-completed edit before the debounce timer.
    canvas('search PersistA');time.sleep(.2);canvas('ungroup')
    unload(save=False);reload()
    check(state()['groups']==[['Twin','Twin']],'ungroup survives immediate unload without manual save')
    # Rebuild the unique group for a new compositor session.
    for c in (a,b): focus(c);canvas('select')
    canvas('group');time.sleep(.5)
    canvas('save-memory')
    expected_titles={c['title']:(c['at'],c['size']) for c in n.clients() if c['title']!='Twin'}
    unload();n.stop();n=None
    n=launch()
    check(all((c['at'],c['size'])==expected_titles[c['title']] for c in n.clients() if c['title'] in expected_titles),'new session restores unique app/title geometry')
    check(any(set(g)=={'PersistA','PersistB'} for g in state()['groups']),'new session restores unique app/title group')
    check(not any('Twin' in g for g in state()['groups']),'ambiguous titles do not restore incorrect group membership in a new session')
    # A damaged record must not prevent valid windows and groups restoring.
    canvas('save-memory')
    unload()
    memory=Path(state_dir.name)/'spatial-overview/canvas-memory.tsv'
    with memory.open('a') as f:
        f.write('window\tbroken\tbroken\tnan\t0\t100\t100\t1\t0\t0\n')
        f.write('camera\tbroken\tinf\t0\t0\t0\t0\t0\t0\n')
    reload()
    check(any(set(g)=={'PersistA','PersistB'} for g in state()['groups']),'damaged records do not discard valid saved groups')
    check(not n.ctl('configerrors'),'configuration valid after restoration')
    print('ALL PASSED',flush=True)
finally:
    if n:n.stop()
    state_dir.cleanup()
