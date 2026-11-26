# Datei-Version: 1.00 (2026-11-26) - test_log_drag.py
# ----------------------------------------------------------------------------------------------
# Name:           test_log_drag.py
# Path:           test_log_drag.py
# Version:        1.00
# Last Update:    2026-11-26
# Author:         Jürgen Winkler
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-26  Neu: Fenster Kompilieren und Hochladen (web_log 1.15) verschieben, waehrend Meldungen eintreffen: Test im echten Browser (Edge oder Chrome ohne Oberflaeche)
# ----------------------------------------------------------------------------------------------
"""Aufruf: python test_log_drag.py

Startet eine kleine NiceGUI-Seite mit dem echten WebLog (_web/web_log.py) und einem Browser ohne Oberflaeche (Edge oder Chrome). Ein Erzeuger schreibt etwa 1000 Zeilen je Sekunde
in das Fenster; gleichzeitig zieht ein Skript im Browser die Titelzeile des Fensters (100 Mausbewegungen in einer Sekunde, danach loslassen). Geprueft wird:
  * das Fenster folgt der Maus (Endposition),
  * waehrend des Ziehens wird das Fenster nicht mit neuen Zeilen belastet (sie werden zurueckgehalten),
  * nach dem Loslassen stehen alle Zeilen im Fenster (keine geht verloren),
  * kein Bild haengt laenger als 250 ms und keine Aufgabe blockiert den Browser laenger als 200 ms.
Zum Vergleich laeuft der Fall ohne Zurueckhalten (altes Verhalten); seine Werte werden nur ausgegeben.
Ohne Edge oder Chrome wird der Test uebersprungen. 'python test_log_drag.py --server <Port> <hold|nohold>' startet nur die Seite."""
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
LINES = 2000

HARNESS_JS = r"""
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const card = document.querySelector('.mll-bottom-card');
  const log = document.querySelector('.mll-log');
  const head = card.querySelector('.row');
  let last = performance.now(), maxGap = 0, frames = 0, running = true;
  const tick = t => { maxGap = Math.max(maxGap, t - last); last = t; frames++; if (running) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  let longest = 0;
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) longest = Math.max(longest, e.duration); }).observe({entryTypes: ['longtask']}); } catch (err) {}
  const count = () => (log.textContent.match(/Zeile \d{4}/g) || []).length;
  await sleep(500);                                           // die Meldungen laufen schon
  const r = head.getBoundingClientRect();
  const cx = r.left + 50, cy = r.top + 10;
  const ev = (type, x, y) => new PointerEvent(type, {clientX: x, clientY: y, pointerId: 1, bubbles: true, button: 0, buttons: 1, pointerType: 'mouse'});
  maxGap = 0; longest = 0;                                    // Messung ab dem Ziehen
  head.dispatchEvent(ev('pointerdown', cx, cy));
  const n0 = count();
  for (let i = 1; i <= 100; i++) { window.dispatchEvent(ev('pointermove', cx - i * 3, cy - i * 2)); await sleep(10); }
  const n1 = count();
  const during = {maxGap: maxGap, longest: longest};
  window.dispatchEvent(ev('pointerup', cx - 300, cy - 200));
  await sleep(2500);
  running = false;
  emitEvent('mll_test_result', {maxGap: during.maxGap, longest: during.longest, grown: n1 - n0, total: count(), pos: window.__mllLogPos, transform: card.style.transform});
})();
"""


def run_server(port, hold):
    import logging
    logging.disable(logging.CRITICAL)
    from nicegui import ui
    from _web import web_dialogs as wd
    from _web import web_log

    if not hold:
        web_log.WebLog.DRAG_HOLD_MAX = 0.0                                    # altes Verhalten: Zeilen auch waehrend des Ziehens anzeigen

    @ui.page("/")
    async def page():
        from nicegui import context
        client = context.client
        loop = asyncio.get_running_loop()
        wd._bridge["client"], wd._bridge["loop"] = client, loop
        ui.label("Hintergrund")
        weblog = web_log.WebLog(None)
        weblog._loop = loop
        done = {"v": False}

        def result(e):
            if not done["v"]:
                done["v"] = True
                print("RESULT:" + json.dumps(e.args), flush=True)
                os._exit(0)
        ui.on("mll_test_result", result)
        await client.connected()
        await weblog._show_async()

        def producer():
            for i in range(LINES):
                weblog.add_text_to_textwindow("Zeile %04d: Kompilieren der Datei src/Beispiel_%d.cpp ..." % (i, i))
                time.sleep(0.001)
        threading.Thread(target=producer, daemon=True).start()
        client.run_javascript(HARNESS_JS)

    ui.run(port=port, reload=False, show=False)


def find_browser():
    for path in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        if os.path.isfile(path):
            return path
    return shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("microsoft-edge")


def measure(port, hold, timeout=60):
    browser = find_browser()
    server = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--server", str(port), "hold" if hold else "nohold"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd=ROOT)
    profile = tempfile.mkdtemp(prefix="mll_edge_")
    edge = None
    try:
        time.sleep(5)                                                         # die Seite startet
        edge = subprocess.Popen([browser, "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=" + profile, "--window-size=1280,900",
                                 "http://localhost:%d/" % port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = {}

        def reader():
            for line in server.stdout:
                if line.startswith("RESULT:"):
                    result.update(json.loads(line[7:]))
                    return
        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        thread.join(timeout)
        return result
    finally:
        for proc in (edge, server):
            if proc is not None and proc.poll() is None:
                proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


@unittest.skipUnless(find_browser(), "kein Edge oder Chrome gefunden")
class DragWithMessagesTests(unittest.TestCase):
    def test_drag_while_messages_arrive(self):
        old = measure(8791, hold=False)
        new = measure(8792, hold=True)
        print("\nOhne Zurueckhalten: %s\nMit Zurueckhalten:  %s" % (old, new))
        self.assertTrue(new, "keine Messwerte vom Browser")
        self.assertAlmostEqual(new["pos"]["x"], -300, delta=2)                # das Fenster folgt der Maus
        self.assertAlmostEqual(new["pos"]["y"], -200, delta=2)
        self.assertEqual(new["grown"], 0, "waehrend des Ziehens kamen Zeilen ins Fenster")
        self.assertEqual(new["total"], LINES, "nach dem Loslassen fehlen Zeilen")
        self.assertLess(new["maxGap"], 250, "ein Bild hing beim Ziehen laenger als 250 ms")
        self.assertLess(new["longest"], 200, "eine Aufgabe blockierte den Browser laenger als 200 ms")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--server":
        run_server(int(sys.argv[2]), sys.argv[3] == "hold")
    else:
        unittest.main(verbosity=2)
