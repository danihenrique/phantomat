"""Compare native and canvas touchpad frames; protect wheel units and stop grouping."""
import importlib.util, subprocess, time, os, json, sys, re
from pathlib import Path
root=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('nav',root/'tests/navigator-nested.py'); nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
nav.WINDOWS=[]
n=nav.Nested(sys.argv[1],root/'.build/scroll-shots')
app=None
try:
 try: n.launch()
 except Exception:
  print(Path(n.log.name).read_text()[-4500:]);raise
 env=n.env(); env['WAYLAND_DEBUG']='client'
 logfile=Path(n.tmp.name)/'scroll-protocol.log'
 log=open(logfile,'w')
 app=subprocess.Popen(['qs','-p',str(root/'tests/scroll-frame.qml')],env=env,stdout=log,stderr=log)
 time.sleep(2)
 print('CLIENTS',[(c['class'],c['at'],c['size']) for c in n.clients()],flush=True)
 for phase in ['native','canvas']:
  if phase=='canvas':
   n.dispatch('hl.plugin.spatialoverview.overview("on all")');time.sleep(1);n.keys('-k','Return');time.sleep(1)
  offset=logfile.stat().st_size
  print('PHASE',phase,flush=True)
  subprocess.run([str(root/'.build/vpointer'),'1280','720','abs','640','360','sleep','200','rel','1','1','sleep','200','finger','2','1','sleep','30','finger','2','1','sleep','30','stop','sleep','200','wheel','1','sleep','200'],env=n.env(),check=True)
  time.sleep(.5)
  frames=[]; frame=[]
  for line in logfile.read_text()[offset:].splitlines():
   if 'wl_pointer#' not in line: continue
   if '.frame()' in line:
    if any('.axis(' in x for x in frame): frames.append(frame)
    frame=[]
   else: frame.append(line)
  stops=[f for f in frames if any('.axis_stop(' in x for x in f)]
  assert len(stops)==1 and sum('.axis_stop(' in x for x in stops[0])==2, f'{phase}: stops split across frames'
  moves=[f for f in frames if not any('.axis_stop(' in x or '.axis_value120(' in x for x in f)]
  assert moves and all(sum('.axis(' in x for x in f)==2 for f in moves), f'{phase}: scroll axes split'
  assert any('.axis_value120(0, 120)' in x for f in frames for x in f), f'{phase}: wheel notch changed'
  print('PASS',phase,'two-axis scroll and stop frames; wheel = 120',flush=True)
 print('PROTOCOL SAVED',flush=True)
finally:
 if app: app.terminate();app.wait(timeout=5)
 n.stop()
