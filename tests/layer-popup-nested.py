"""Check layer-shell popup rendering and clicks before and during canvas."""
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
    for phase in ['native', 'overview', 'canvas']:
        if phase == 'overview':
            n.dispatch('hl.plugin.spatialoverview.overview("on all")')
            time.sleep(1)
        if phase == 'canvas':
            n.keys('-k', 'Return')
            time.sleep(1)
        raw = subprocess.check_output(['grim', '-t', 'ppm', '-'], env=n.env())
        px = raw.split(b'\n', 3)[3]
        magenta = sum(1 for i in range(0, len(px)-2, 3) if px[i] > 220 and px[i+1] < 30 and px[i+2] > 220)
        n.shot(phase)
        print(f'{phase}: {magenta} popup pixels', flush=True)
        assert magenta > 10000, f'{phase}: layer popup missing'
        def clicks():
            return int(subprocess.check_output([
                'qs', 'ipc', '-p', str(Path(__file__).with_name('layer-popup.qml').resolve()),
                'call', 'test', 'clicks'], env=n.env(), text=True, timeout=5).strip())
        before = clicks()
        # Popup center is outside its 30px-high parent layer surface.
        subprocess.run([str(nav.ROOT / '.build/vpointer'), '1280', '720',
                        'abs', '180', '100', 'sleep', '200',
                        'down', 'sleep', '80', 'up', 'sleep', '150',
                        'rdown', 'sleep', '80', 'rup', 'sleep', '150'],
                       env=n.env(), check=True, timeout=5)
        after = clicks()
        print(f'{phase}: {after - before} popup clicks', flush=True)
        assert after == before + 2, f'{phase}: popup clicks intercepted'
    print('PASS layer popup remains visible and clickable on canvas', flush=True)
finally:
    if app:
        app.terminate(); app.wait(timeout=5)
    n.stop()
