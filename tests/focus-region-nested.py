"""Regression: focus on one physical half of a single tall output.
Runs only in a nested compositor; never changes the real desktop config.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('nav', root / 'tests/navigator-nested.py')
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)
nav.WINDOWS = [('foot', 'PanelTestA'), ('foot', 'PanelTestB')]
os.environ['NESTED_MODE'] = '960x1080@60'
n = nav.Nested(str(root / 'spatialoverview.so'), str(root / '.build/focus-shots'), extra=',hover_focus=false')

def configure(monitor, rows, row):
    n.ctl('eval', 'hl.config({plugin={spatialoverview={canvas={focus_monitor=' + json.dumps(monitor) + ',focus_rows=' + str(rows) + ',focus_row=' + str(row) + '}}}})')

def land(title):
    n.dispatch('hl.plugin.spatialoverview.canvas(' + json.dumps('search ' + title) + ')')
    time.sleep(.5)
    n.keys('-k', 'Return')
    time.sleep(.8)

def check(title, expected_y, oversize=False):
    for _ in range(30):
        c = next(c for c in n.clients() if c['title'] == title)
        s = json.loads(n.ctl('spatialoverview'))['screens'][0]
        y = c['at'][1] - s['view'][1]
        actual = y if oversize else y + c['size'][1] / 2
        if abs(actual - expected_y) < 5 and abs(s['zoom'] - 1) < .01:
            break
        time.sleep(.1)
    assert abs(actual - expected_y) < 5, (title, actual, expected_y, s, c['at'], c['size'])
    assert abs(s['zoom'] - 1) < .01
    print('PASS', title, 'screen y', actual, flush=True)

try:
    n.launch()
    info = json.loads(n.ctl('monitors', '-j'))[0]
    monitor = info['name']
    height = info['height'] / info['scale']
    print('Test monitor:', info['width'], height, flush=True)
    n.dispatch('hl.plugin.spatialoverview.overview("toggle all")')
    time.sleep(.8)
    for title, x in [('PanelTestA', 0), ('PanelTestB', 1400)]:
        n.dispatch('hl.dsp.window.resize({x=200,y=100,window="title:' + title + '"})')
        n.dispatch('hl.dsp.window.move({x=' + str(x) + ',y=200,window="title:' + title + '"})')
    configure('', 1, 0)
    land('PanelTestA'); check('PanelTestA', height/2)
    configure(monitor, 2, 0)
    land('PanelTestA'); check('PanelTestA', height/4)
    configure(monitor, 2, 1)
    land('PanelTestA'); check('PanelTestA', height*3/4)
    land('PanelTestB'); check('PanelTestB', height*3/4)
    land('PanelTestA'); check('PanelTestA', height*3/4)
    n.dispatch('hl.plugin.spatialoverview.navigate("right")')
    time.sleep(.8)
    check('PanelTestB', height*3/4)
    configure('OTHER-OUTPUT', 2, 1)
    land('PanelTestA'); check('PanelTestA', height/2)
    configure(monitor, 2, -1)
    # Position determines the half even when another window occupies it.
    # Cover above/below the viewport, visible halves and return to same window.
    for relative_y in (-1, .25, .75, 2):
        view = json.loads(n.ctl('spatialoverview'))['screens'][0]['view']
        row = 0 if relative_y < .5 else 1
        x, y = round(view[0]+2000), round(view[1]+relative_y*height-50)
        n.dispatch('hl.dsp.window.move({x=' + str(view[0]+100) + ',y=' + str(view[1]+row*height/2+30) + ',window="title:PanelTestB"})')
        n.dispatch('hl.dsp.window.move({x=' + str(x) + ',y=' + str(y) + ',window="title:PanelTestA"})')
        time.sleep(.5)
        land('PanelTestA'); check('PanelTestA', height*(.25 if row == 0 else .75))
        before = next(c['at'] for c in n.clients() if c['title'] == 'PanelTestA')
        land('PanelTestA'); check('PanelTestA', height*(.25 if row == 0 else .75))
        after = next(c['at'] for c in n.clients() if c['title'] == 'PanelTestA')
        assert before == after, ('world position changed', before, after)
    # Directional navigation must use the same spatial rule.
    view = json.loads(n.ctl('spatialoverview'))['screens'][0]['view']
    a = next(c for c in n.clients() if c['title'] == 'PanelTestA')
    n.dispatch('hl.dsp.window.move({x=' + str(a['at'][0]) + ',y=' + str(round(view[1]-height)) + ',window="title:PanelTestB"})')
    time.sleep(1.5)
    n.dispatch('hl.plugin.spatialoverview.navigate("up")')
    time.sleep(.8)
    check('PanelTestB', height/4)
    n.dispatch('hl.plugin.spatialoverview.navigate("down")')
    time.sleep(.8)
    check('PanelTestA', height*3/4)
    configure(monitor, 2, 1)
    n.dispatch('hl.dsp.window.resize({x=400,y=700,window="title:PanelTestA"})')
    land('PanelTestA'); check('PanelTestA', height/2, oversize=True)
    assert not n.ctl('configerrors')
    print('ALL PASSED', flush=True)
except Exception:
    if getattr(n, 'log', None):
        n.log.flush()
        print(Path(n.log.name).read_text()[-7000:], flush=True)
    raise
finally:
    n.stop()
