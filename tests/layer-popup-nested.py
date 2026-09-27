"""Check layer-shell popup rendering before and during persistent canvas."""
import importlib.util, os, subprocess, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location('nav', Path(__file__).with_name('navigator-nested.py'))
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.WINDOWS = [('foot', 'layer-popup-test')]
n = nav.Nested(sys.argv[1], '.build/shots-layer-popup')
app = None
try:
    try:
        n.launch()
    except Exception:
        print(Path(n.log.name).read_text()[-7000:])
        raise
    app = subprocess.Popen(['qs', '-p', str(Path(__file__).with_name('layer-popup.qml').resolve())], env=n.env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    for phase in ['native', 'canvas']:
        if phase == 'canvas':
            n.dispatch('hl.plugin.spatialoverview.overview("on all")')
            time.sleep(1)
            n.keys('-k', 'Return')
            time.sleep(1)
        raw = subprocess.check_output(['grim', '-t', 'ppm', '-'], env=n.env())
        px = raw.split(b'\n', 3)[3]
        magenta = sum(1 for i in range(0, len(px)-2, 3) if px[i] > 220 and px[i+1] < 30 and px[i+2] > 220)
        n.shot(phase)
        print(f'{phase}: {magenta} popup pixels', flush=True)
        assert magenta > 10000, f'{phase}: layer popup missing'
    print('PASS layer popup remains visible on canvas', flush=True)
finally:
    if app:
        app.terminate(); app.wait(timeout=5)
    n.stop()
