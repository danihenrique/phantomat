"""Upgrade from a pre-persistence plugin without losing live groups/layout."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('nav', ROOT/'tests/navigator-nested.py')
nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
nav.WINDOWS=[('foot','UpgradeA'),('foot','UpgradeB'),('foot','UpgradeC')]
old=Path(sys.argv[1]).resolve();new=ROOT/'spatialoverview.so'
n=nav.Nested(str(old),str(ROOT/'.build/migration-shots'),extra=',remember_layout=true,groups=true,hover_focus=false,snap_enabled=false')
def canvas(action):n.dispatch('hl.plugin.spatialoverview.canvas('+json.dumps(action)+')')
def state():return json.loads(n.ctl('spatialoverview'))
def geometry():return {c['address']:(c['at'],c['size']) for c in n.clients()}
def check(ok,text):
    assert ok,text
    print('PASS',text,flush=True)
try:
    n.launch();n.dispatch('hl.plugin.spatialoverview.overview("on all")');time.sleep(1)
    for c in n.clients():
        n.dispatch('hl.dsp.focus({window="address:'+c['address']+'"})');canvas('select')
    canvas('group')
    for i,c in enumerate(n.clients()):
        n.dispatch('hl.dsp.window.resize({x='+str(280+i*30)+',y='+str(220+i*60)+',window="address:'+c['address']+'"})')
        n.dispatch('hl.dsp.window.move({x='+str(-1000+i*410)+',y='+str(200+i*350)+',window="address:'+c['address']+'"})')
    time.sleep(.8);canvas('search UpgradeA');n.keys('-k','Return');time.sleep(1)
    before=state();boxes=geometry()
    env=n.env();env['HYPRLAND_INSTANCE_SIGNATURE']=n.sig;env['XDG_STATE_HOME']=n.state
    subprocess.run(['bash','-e','-c','project_dir='+str(ROOT)+'\nsource scripts/common.sh\nremember_canvas_layout\nsafe_unload'],cwd=ROOT,env=env,check=True,timeout=40)
    cfg=Path(n.tmp.name)/'nested.lua';cfg.write_text(cfg.read_text().replace(str(old),str(new)))
    n.ctl('plugin','load',str(new));n.ctl('reload');time.sleep(.5)
    n.dispatch('hl.plugin.spatialoverview.overview("on all")');time.sleep(1.2)
    after=state()
    check(after['memory_version']==2,'new plugin is loaded')
    check(geometry()==boxes,'migration preserves every position and size')
    check(sorted(before['groups'][0])==sorted(after['groups'][0]),'migration preserves all three group members')
    a,b=before['screens'][0],after['screens'][0]
    check(abs(a['zoom']-b['zoom'])<.002 and all(abs(x-y)<=2 for x,y in zip(a['view'],b['view'])),'migration preserves camera and group fit zoom')
    check(not n.ctl('configerrors'),'migrated config is valid')
    print('ALL PASSED',flush=True)
finally:n.stop()
