# Datei-Version: 1.00 (2026-11-15) - web_simulator.py
# ----------------------------------------------------------------------------------------------
# Name:           web_simulator.py
# Path:           _web/web_simulator.py
# Version:        1.00
# Last Update:    2026-11-15
# Author:         Harold Linke
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-15  Neu: Anzeige des LED-Simulators im Browser (Linux; unter Windows zeichnet die DLL ein eigenes Fenster)
# ----------------------------------------------------------------------------------------------
"""LED-Simulator im Browser.

Die Simulation selbst liegt in libMobaLedLibWrapper.so (simulator_linux/, ohne Fenster). Dieses Modul zeichnet die LED-Farben in ein schwebendes
Feld der Seite: Ein Zeitgeber (alle 100 ms) holt ueber M39_Simulator.sim_frame() die Farben und schickt sie an ein Canvas. Das Feld erscheint,
wenn der Simulator geoeffnet ist (Simulator-Option 1 bis 3 oder Zum Arduino schicken), und verschwindet, wenn er geschlossen wird.
Aufruf in build_page: web_simulator.attach()."""
import json
import logging
import platform

from nicegui import ui

logger = logging.getLogger(__name__)

JS = """
<script>
window.mllSimDraw = function (id, d) {
  var c = document.getElementById(id); if (!c) return;
  var size = d.size, sp = 2, b = 8;
  var w = d.x * (size + sp) + b * 2, h = d.y * (size + sp) + b * 2;
  if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
  var g = c.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, w, h);
  function cc(v) { return v === 0 ? 0 : Math.round(80 + v * 175 / 255); }
  for (var y = 0; y < d.y; y++) {
    for (var x = 0; x < d.x; x++) {
      var xx = (d.snake && (y % 2 === 1)) ? d.x - x - 1 : x;
      var idx = d.offset + y * d.x + xx; if (idx * 3 + 2 >= d.rgb.length) continue;
      var px = b + x * (size + sp) + size / 2, py = b + y * (size + sp) + size / 2;
      g.beginPath(); g.arc(px, py, size / 2, 0, 6.2832);
      g.fillStyle = 'rgb(' + cc(d.rgb[idx * 3]) + ',' + cc(d.rgb[idx * 3 + 1]) + ',' + cc(d.rgb[idx * 3 + 2]) + ')';
      g.fill(); g.strokeStyle = '#404040'; g.lineWidth = 1; g.stroke();
      if (d.numbers) { g.fillStyle = '#a0a0a0'; g.font = '9px sans-serif'; g.fillText(String(idx), px - size / 2 + 2, py + size / 2 - 2); }
    }
  }
};
</script>
"""


def attach():
    """Schwebendes Simulatorfeld in die Seite einbauen (nur Linux; sonst nichts)."""
    if platform.system() != "Linux":
        return
    import proggen.M39_Simulator as M39
    ui.add_head_html(JS)
    state = {"numbers": False, "snake": False}
    canvas_id = "mll-sim-canvas"
    with ui.card().classes("p-2").style("position:fixed; right:12px; bottom:12px; z-index:2000; display:none; background:#111; color:#ddd") as card:
        with ui.row().classes("items-center justify-between no-wrap w-full"):
            ui.label("LED Simulator").classes("text-sm")
            ui.button(icon="close", on_click=lambda: M39.CloseSimulator()).props("flat dense round size=sm color=white")
        ui.html('<canvas id="%s" style="max-width:90vw"></canvas>' % canvas_id)
        with ui.row().classes("items-center no-wrap"):
            ui.checkbox("LED-Nummern", on_change=lambda e: state.update(numbers=bool(e.value))).props("dense dark")
            ui.checkbox("S-Verdrahtung", on_change=lambda e: state.update(snake=bool(e.value))).props("dense dark")
    shown = {"v": False}

    def tick():
        try:
            visible = M39.MobaLedLibWrapper is not None and bool(M39.IsLEDWindowVisible())
        except BaseException:                                  # noqa: BLE001
            visible = False
        if visible != shown["v"]:
            shown["v"] = visible
            card.style("display:block" if visible else "display:none")
        if not visible:
            return
        rgb = M39.sim_frame()
        if rgb is None:
            return
        p = M39.sim_params
        data = {"x": p.get("x", 8), "y": p.get("y", 8), "size": p.get("size", 24), "offset": p.get("offset", 0),
                "rgb": rgb, "numbers": state["numbers"], "snake": state["snake"]}
        ui.run_javascript("window.mllSimDraw(%s, %s)" % (json.dumps(canvas_id), json.dumps(data)))

    ui.timer(0.1, tick)
