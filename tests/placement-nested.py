#!/usr/bin/env python3
"""New-window geometry, panned cameras, reopen memory and workspace ownership."""
import importlib.util, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location("nav", ROOT/"tests/navigator-nested.py")
nav=importlib.util.module_from_spec(spec); spec.loader.exec_module(nav); nav.WINDOWS=[]
n=nav.Nested(sys.argv[1], ROOT/".build/shots-placement", extra=",workspace_isolation=true,placement_near_view=true,snap_enabled=true,remember_layout=true")
def spawn(title):
 n.dispatch('hl.dsp.exec_cmd('+json.dumps('foot --app-id='+title+' --title='+title+' /usr/bin/cat')+')')
 for _ in range(60):
  matches=[c for c in n.clients() if c['title']==title]
  if matches: time.sleep(.5); return next(c for c in n.clients() if c['title']==title)
  time.sleep(.1)
 raise AssertionError('window failed to map')
def box(c): return c['at']+c['size']
def area(a,b): return max(0,min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0]))*max(0,min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]))
def view(): return json.loads(n.ctl('spatialoverview'))['screens'][0]['view']
def canvas(a): n.dispatch('hl.plugin.spatialoverview.canvas('+json.dumps(a)+')'); time.sleep(.7)
try:
 n.launch(); spawn('Seed')
 n.dispatch('hl.plugin.spatialoverview.overview("on all")'); time.sleep(1)
 started=time.monotonic()
 canvas('viewport -5000 -6000')
 before=view(); first=spawn('Fresh')
 assert area(box(first),before)>0, (box(first),before)
 print('PASS new window intersects the panned viewport',flush=True)
 for i in range(6):
  c=spawn('Row'+str(i))
  for other in n.clients():
   if other['address']!=c['address'] and other['workspace']['id']==c['workspace']['id']:
    assert area(box(c),box(other))==0, (c['title'],other['title'],box(c),box(other))
 print('PASS successive launches do not overlap, including snap-enabled mode',flush=True)
 old=next(c for c in n.clients() if c['title']=='Fresh'); position=old['at']; workspace=old['workspace']['id']
 n.dispatch('hl.dsp.focus({workspace="3"})'); time.sleep(.7)
 n.dispatch('hl.dsp.focus({window="address:'+old['address']+'"})'); time.sleep(.7)
 after=next(c for c in n.clients() if c['address']==old['address'])
 assert after['workspace']['id']==workspace and after['at']==position
 print('PASS cross-workspace activation preserves owner and position',flush=True)
 canvas('save-memory')
 n.dispatch('hl.dsp.window.close({window="address:'+old['address']+'"})'); time.sleep(.5)
 # Wait out the intentional startup/session-restore grace period.
 time.sleep(max(0,47-(time.monotonic()-started)))
 canvas('viewport 7000 8000'); before=view(); reopened=spawn('Fresh')
 assert area(box(reopened),before)>0, (box(reopened),before)
 print('PASS reopened app uses current view instead of distant saved position',flush=True)
 n.shot('placement')
except Exception:
 if getattr(n,"log",None):
  n.log.flush(); print(Path(n.log.name).read_text()[-6000:],flush=True)
 raise
finally: n.stop()
