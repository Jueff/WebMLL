# Datei-Version: 1.14 (2026-11-25) - web_form_other.py
# ----------------------------------------------------------------------------------------------
# Name:           web_form_other.py
# Path:           _web/web_form_other.py
# Version:        1.14
# Last Update:    2026-11-25
# Author:         Harold Linke
# Licence:        LGPL V2.1
# History of Change:
#   1.14  2026-11-25  Tooltip der einzigen Zielvariable: Eingabe des Namens fuer Zustand 0 (zum Beispiel Test0), die weiteren Zustaende heissen Test1, Test2 ... Zeilen mit '# v1.14'
#   1.13  2026-11-25  Mini-Farbtest aus dem Parameterformular: LED-Nummer 0 und LED-Kanal 0 voreingestellt (nur die Heartbeat-LED bekommt die Farbe), der Anwender kann die LED von Hand einstellen. Zeilen mit '# v1.13'
#   1.12  2026-11-25  Die Bezeichnung 'Zielvariable' (ohne 1) gilt auch in den Fehlermeldungen. Zeilen mit '# v1.12'
#   1.11  2026-11-25  Parameterformular: 0/1-Flags als Ein/Aus-Schalter, RGB-Farben als Textfeld mit Taste 'Farbe waehlen' (Mini-Farbtest) und Farbfeldern, 'Zielvariable 1' heisst bei nur einer Zielvariable 'Zielvariable'. Zeilen mit '# v1.11'
#   1.10  2026-11-24  LED Kanal Auswahl als farbige Tasten (Gelb, Zyan, Rot, Gruen, Blau) statt Auswahlkreise. Zeilen mit '# v1.10'
#   1.09  2026-11-24  Zahlenfelder mit fester Breite (Zahl sichtbar neben dem Regler), LED Channel als Zahlenfeld mit minus/plus wie die ms-Felder, Mausrad ueber Zahlenfeld und Regler aendert den Wert. Zeilen mit '# v1.09'
#   1.08  2026-11-24  Eingabe der Parameter: Zahlenwerte mit Minimum und Maximum (Spannweite bis 1000) als Schieberegler mit Zahlenfeld und Tasten minus und plus, Zeitwerte als Felder Min, Sek und ms, der HSV-Farbwert (HSVColor) mit Regler im Farbverlauf und Farbfeld (Umrechnung wie hsv2rgb_rainbow der MobaLedLib). Der Wert bleibt derselbe Text wie vorher, die Pruefungen des Originals sind unveraendert. Zeilen mit '# v1.08'
#   1.07  2026-11-05  Die Auswahlpruefung (Wert in der Liste, sonst Rueckfall auf den Standardwert mit Meldung) gilt nur fuer den Typ List, nicht fuer Mode (Flags wie OptCtrPar haben keine feste Liste; Korrektur des Entwicklers) (fruehere Versionen ohne Eintrag)
# ----------------------------------------------------------------------------------------------
"""Web-Ersatz fuer proggen/Userform_Other.py (Parameterformular fuer Makros ohne Sonderformular).

Die Klasse WebUserFormOther erbt von UserForm_Other und ersetzt nur Show_UserForm_Other:
  * Die Vorbereitung der Parameter (alte Werte, Optionen, Listen, Standardwerte) ist aus dem Original
    uebernommen, nur ohne Tk-Widgets.
  * Der Dialog laeuft im Browser. Die Pruefungen (Create_Result -> Check_Par_with_ErrMsg, Bereiche,
    Zeitangaben, RGB-Listen ...) sind unveraendert die des Originals; die Eingabewerte werden dafuer in
    kleinen Variablenobjekten bereitgestellt, die wie die Tk-Variablen ein get() haben.
  * Bei einer Fehleingabe erscheint wie im Original die Fehlermeldung, danach bleibt der Dialog aber offen
    (das Original schliesst ihn ohne Ergebnis).
Im Hauptthread (kein Worker) wird das Tk-Original verwendet.
"""
from __future__ import annotations

import logging
import re  # v1.11
import sys

from _web import web_dialogs as wd

logger = logging.getLogger(__name__)

LED_OPTION_LABELS = {"1": "Alle", "2": "1&2 / Gelb", "3": "2&3 / Zyan",
                     "4": "1 / Rot", "5": "2 / Grün", "6": "3 / Blau"}
MLL_TYPE_TO_WIDGET = {"Mode": "String", "SheetName": "String", "Var": "String", "CmpMod": "String",
                      "MB_LED": "String", "List": "List", "Time": "Time", "RGB": "String", "RGB2": "String",
                      "PinNr": "String", "PinLst": "String", "InpVar": "String", "GVarNr": "String",
                      "OutList": "String", "Logic": "BigEntry", "Cx": "String", "#": "String"}


# ------------------------------------------------------------------ reine Hilfsfunktionen
class Var:
    """Ersatz fuer tk.StringVar: nur get()/set()."""
    def __init__(self, value=""):
        self._v = value

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


def available_led_options(led_channels: int) -> list[str]:
    """Welche der Optionsfelder 1..6 angeboten werden (Logik aus Show_UserForm_Other)."""
    all_, o12, o23, c1 = True, True, True, True
    if led_channels == -1:
        all_ = o12 = o23 = False
    elif led_channels == -2:
        all_ = False
    elif led_channels == 2:
        all_ = False
    opts = []
    if all_:
        opts.append("1")
    if o12:
        opts.append("2")
    if o23:
        opts.append("3")
    if c1:
        opts += ["4", "5", "6"]
    return opts


def option_value_for(val: str, only_single: bool):
    """Logik aus Set_OptionButton: bestehende Kanalbezeichnung -> Wert des Optionsfeldes (None = unbekannt)."""
    table = {"C_ALL": "4" if only_single else "1", "C1": "4", "C2": "5", "C3": "6",
             "C12": "4" if only_single else "2", "C23": "5" if only_single else "3"}
    return table.get(val)


def norm(x):
    """CRange/Zelle -> Wert; None -> ''."""
    if hasattr(x, "Value"):
        x = x.Value
    return "" if x is None else x



# ------------------------------------------------------------------ Hilfsfunktionen fuer die Eingabe (v1.08)
SLIDER_MAX_SPAN = 1000                                                                       # v1.08: Zahlenwerte mit groesserer Spannweite bleiben Textfelder


def _scale8(i: int, scale: int) -> int:  # v1.08
    return (i * (scale + 1)) >> 8  # v1.08


def hsv_rainbow(hue: int) -> tuple:  # v1.08
    """Farbton 0..255 (Saettigung und Helligkeit 255) wie hsv2rgb_rainbow der MobaLedLib (libraries/MobaLedLib/src/PicoFastLED.cpp, Y1=1). Rueckgabe (r, g, b)."""  # v1.08
    hue = int(hue) & 0xFF  # v1.08
    offset8 = (hue & 0x1F) << 3  # v1.08
    third = _scale8(offset8, 256 // 3)  # v1.08
    twothirds = _scale8(offset8, (256 * 2) // 3)  # v1.08
    if not hue & 0x80:  # v1.08
        if not hue & 0x40:  # v1.08
            if not hue & 0x20:  # v1.08
                return 255 - third, third, 0  # Rot nach Orange  # v1.08
            return 171, 85 + third, 0  # Orange nach Gelb  # v1.08
        if not hue & 0x20:  # v1.08
            return 171 - twothirds, 170 + third, 0  # Gelb nach Gruen  # v1.08
        return 0, 255 - third, third  # Gruen nach Aqua  # v1.08
    if not hue & 0x40:  # v1.08
        if not hue & 0x20:  # v1.08
            return 0, 171 - twothirds, 85 + twothirds  # Aqua nach Blau  # v1.08
        return third, 0, 255 - third  # Blau nach Violett  # v1.08
    if not hue & 0x20:  # v1.08
        return 85 + third, 0, 171 - third  # Violett nach Rosa  # v1.08
    return 170 + third, 0, 85 - third  # Rosa nach Rot  # v1.08


def hue_hex(hue: int) -> str:  # v1.08
    r, g, b = hsv_rainbow(hue)  # v1.08
    return "#%02x%02x%02x" % (r, g, b)  # v1.08


def hue_gradient_css() -> str:  # v1.08
    """CSS-Farbverlauf ueber alle Farbtoene 0..255 (Hintergrund des Reglers)."""  # v1.08
    return "linear-gradient(to right, " + ", ".join(hue_hex(h) for h in range(0, 256, 8)) + ", " + hue_hex(255) + ")"  # v1.08


def parse_int(text):  # v1.08
    """'12', ' -3 ' -> Zahl; sonst None (zum Beispiel ein Variablenname)."""  # v1.08
    t = str(text).strip()  # v1.08
    if t.lstrip("-").isdigit():  # v1.08
        return int(t)  # v1.08
    return None  # v1.08


def slider_range(mn, mx, current):  # v1.08
    """(min, max, wert), wenn der Parameter als Schieberegler mit Zahlenfeld gezeigt werden kann, sonst None."""  # v1.08
    lo, hi, val = parse_int(mn), parse_int(mx), parse_int(current)  # v1.08
    if lo is None or hi is None or val is None or hi <= lo or hi - lo > SLIDER_MAX_SPAN:  # v1.08
        return None  # v1.08
    return lo, hi, min(max(val, lo), hi)  # v1.08


_TIME_UNITS = {"min": 60000.0, "sek": 1000.0, "sec": 1000.0, "ms": 1.0}  # v1.08


def parse_time_ms(text):  # v1.08
    """Zeitangabe ('1 Sek', '0.5 Sec', '2 Min', '100 ms', '250') in Millisekunden; None, wenn nicht lesbar. Eine Zahl ohne Einheit sind Millisekunden (wie im Original)."""  # v1.08
    t = str(text).strip().replace(",", ".")  # v1.08
    parts = t.split()  # v1.08
    try:  # v1.08
        if len(parts) == 1:  # v1.08
            return int(float(parts[0]) + 0.5)  # v1.08
        if len(parts) == 2 and parts[1].lower() in _TIME_UNITS:  # v1.08
            return int(float(parts[0]) * _TIME_UNITS[parts[1].lower()] + 0.5)  # v1.08
    except ValueError:  # v1.08
        pass  # v1.08
    return None  # v1.08


def format_time_ms(ms: int) -> str:  # v1.08
    """Millisekunden als Zeitangabe mit der groessten passenden ganzen Einheit: 1000 -> '1 Sek', 90000 -> '90 Sek', 120000 -> '2 Min', 1500 -> '1500 ms'."""  # v1.08
    ms = int(ms)  # v1.08
    if ms > 0 and ms % 60000 == 0:  # v1.08
        return f"{ms // 60000} Min"  # v1.08
    if ms > 0 and ms % 1000 == 0:  # v1.08
        return f"{ms // 1000} Sek"  # v1.08
    return f"{ms} ms"  # v1.08


class _Holder:  # v1.08
    """Ersetzt ein NiceGUI-Eingabefeld fuer collect(): value liefert den Text des Parameters (wie vorher ein Textfeld)."""  # v1.08
    def __init__(self, getter):  # v1.08
        self._getter = getter  # v1.08

    @property
    def value(self):  # v1.08
        return self._getter()  # v1.08


def _wheel(ui, widget, num, mn, mx, step):  # v1.09
    """Mausrad ueber dem Widget aendert das Zahlenfeld (Rad nach oben = plus). Die Seite scrollt dabei nicht."""  # v1.09
    def on_wheel(e):  # v1.09
        dy = (e.args or {}).get("deltaY", 0) or 0  # v1.09
        if dy:  # v1.09
            cur = int(num.value or 0)  # v1.09
            num.set_value(min(mx, cur + step) if dy < 0 else max(mn, cur - step))  # v1.09
    widget.on("wheel.prevent", on_wheel, args=["deltaY"])  # v1.09


def _stepper(ui, value, mn, mx, step=1, width="w-36", wheel_on=None):  # v1.09
    """Zahlenfeld mit den Tasten minus und plus (wie im Excel-Programm), feste Breite, Mausrad."""  # v1.09
    num = ui.number(value=value, min=mn, max=mx, step=step, format="%d").props("dense outlined input-class=text-center").classes(width + " shrink-0")  # v1.09
    _wheel(ui, num, num, mn, mx, step)  # v1.09
    with num.add_slot("prepend"):  # v1.08
        ui.button(icon="remove", on_click=lambda: num.set_value(max(mn, int(num.value or 0) - step))).props("flat dense round size=sm")  # v1.08
    with num.add_slot("append"):  # v1.08
        ui.button(icon="add", on_click=lambda: num.set_value(min(mx, int(num.value or 0) + step))).props("flat dense round size=sm")  # v1.08
    return num  # v1.08


def _add_number_row(ui, p, cur, rng):  # v1.08
    """Schieberegler und Zahlenfeld mit minus/plus, beide immer gleich. Rueckgabe: Holder mit dem Wert als Text."""  # v1.08
    lo, hi, val = rng  # v1.08
    state = {"busy": False}  # v1.08
    with ui.row().classes("w-full items-center no-wrap gap-3"):  # v1.08
        ui.label(p["title"]).classes("w-48 shrink-0")  # v1.08
        slider = ui.slider(min=lo, max=hi, step=1, value=val).props("label").classes("grow")  # v1.08
        num = _stepper(ui, val, lo, hi)  # v1.08
        _wheel(ui, slider, num, lo, hi, 1)  # v1.09

    def clamp(v):  # v1.08
        try:  # v1.08
            return min(max(int(v), lo), hi)  # v1.08
        except (TypeError, ValueError):  # v1.08
            return lo  # v1.08

    def from_slider(e):  # v1.08
        if not state["busy"]:  # v1.08
            state["busy"] = True  # v1.08
            num.set_value(clamp(e.value))  # v1.08
            state["busy"] = False  # v1.08

    def from_num(e):  # v1.08
        if not state["busy"] and e.value is not None:  # v1.08
            state["busy"] = True  # v1.08
            slider.set_value(clamp(e.value))  # v1.08
            state["busy"] = False  # v1.08
    slider.on_value_change(from_slider)  # v1.08
    num.on_value_change(from_num)  # v1.08
    if p["tooltip"]:  # v1.08
        num.tooltip(p["tooltip"])  # v1.08
    return _Holder(lambda: str(clamp(num.value)))  # v1.08


def _add_hue_row(ui, p, cur):  # v1.08
    """HSV-Farbwert: Regler im Farbverlauf, Zahlenfeld mit minus/plus und ein Feld mit der eingestellten Farbe."""  # v1.08
    val = min(max(parse_int(cur) or 0, 0), 255)  # v1.08
    try:  # v1.08
        ui.add_css(".mll-hue .q-slider__track-container { background: %s !important; height: 12px !important; opacity: 1 !important; }"
                   " .mll-hue .q-slider__track { background: transparent !important; }" % hue_gradient_css())  # v1.08
    except Exception:                                      # noqa: BLE001  # v1.08
        logger.debug("CSS fuer den Farbregler nicht gesetzt", exc_info=True)  # v1.08
    state = {"busy": False}  # v1.08
    with ui.row().classes("w-full items-center no-wrap gap-3"):  # v1.08
        ui.label(p["title"]).classes("w-48 shrink-0")  # v1.08
        slider = ui.slider(min=0, max=255, step=1, value=val).props("label color=transparent track-color=transparent selection-color=transparent inner-track-color=transparent").classes("grow mll-hue")  # v1.08
        num = _stepper(ui, val, 0, 255)  # v1.08
        _wheel(ui, slider, num, 0, 255, 1)  # v1.09
        swatch = ui.element("div").style("width: 44px; height: 32px; border: 1px solid #888; border-radius: 4px; background: %s" % hue_hex(val))  # v1.08

    def clamp(v):  # v1.08
        try:  # v1.08
            return min(max(int(v), 0), 255)  # v1.08
        except (TypeError, ValueError):  # v1.08
            return 0  # v1.08

    def show(v):  # v1.08
        swatch.style("background: %s" % hue_hex(clamp(v)))  # v1.08

    def from_slider(e):  # v1.08
        if not state["busy"]:  # v1.08
            state["busy"] = True  # v1.08
            num.set_value(clamp(e.value))  # v1.08
            state["busy"] = False  # v1.08
        show(e.value)  # v1.08

    def from_num(e):  # v1.08
        if not state["busy"] and e.value is not None:  # v1.08
            state["busy"] = True  # v1.08
            slider.set_value(clamp(e.value))  # v1.08
            state["busy"] = False  # v1.08
            show(e.value)  # v1.08
    slider.on_value_change(from_slider)  # v1.08
    num.on_value_change(from_num)  # v1.08
    if p["tooltip"]:  # v1.08
        num.tooltip(p["tooltip"])  # v1.08
    return _Holder(lambda: str(clamp(num.value)))  # v1.08


def _add_time_row(ui, p, cur, ms):  # v1.08
    """Zeitwert als drei Zahlenfelder Min, Sek und ms mit minus/plus (wie im Excel-Programm). Ein Ueberlauf wird weitergegeben (1000 ms = 1 Sek)."""  # v1.08
    mx = parse_time_ms(p.get("mx", "")) if p.get("mx", "") != "" else None  # v1.08
    top = mx if mx else 35 * 60000  # v1.08
    state = {"busy": False}  # v1.08
    with ui.row().classes("w-full items-center no-wrap gap-2"):  # v1.08
        ui.label(p["title"]).classes("w-48 shrink-0")  # v1.08
        fields = {}  # v1.08
        parts = divmod(max(ms, 0), 60000)  # v1.08
        mins, rest = parts  # v1.08
        secs, msec = divmod(rest, 1000)  # v1.08
        for key, unit, v, hi, step in (("min", "Min", mins, max(top // 60000, 0), 1), ("sec", "Sek", secs, 59, 1), ("ms", "ms", msec, 999, 10)):  # v1.08
            if key == "min" and top < 60000:  # v1.08: der Maximalwert ist unter einer Minute: kein Feld
                continue  # v1.08
            if key == "sec" and top < 1000:  # v1.08
                continue  # v1.08
            fields[key] = _stepper(ui, v, 0, 99999999, step, "w-36")  # v1.08
            ui.label(unit).classes("text-grey-8")  # v1.08
    mult = {"min": 60000, "sec": 1000, "ms": 1}  # v1.08

    def total():  # v1.08
        t = 0  # v1.08
        for k, f in fields.items():  # v1.08
            try:  # v1.08
                t += max(int(f.value or 0), 0) * mult[k]  # v1.08
            except (TypeError, ValueError):  # v1.08
                pass  # v1.08
        return t  # v1.08

    def normalize(_e=None):  # v1.08
        if state["busy"]:  # v1.08
            return  # v1.08
        t = total()  # v1.08
        want = {"min": t // 60000, "sec": (t % 60000) // 1000, "ms": t % 1000}  # v1.08
        if "min" not in fields:  # v1.08
            want["sec"] = t // 1000  # v1.08
        if "sec" not in fields:  # v1.08
            want["ms"] = t  # v1.08
        state["busy"] = True  # v1.08
        try:  # v1.08
            for k, f in fields.items():  # v1.08
                if f.value != want[k]:  # v1.08
                    f.set_value(want[k])  # v1.08
        finally:  # v1.08
            state["busy"] = False  # v1.08
    for f in fields.values():  # v1.08
        f.on_value_change(normalize)  # v1.08
        if p["tooltip"]:  # v1.08
            f.tooltip(p["tooltip"])  # v1.08
    return _Holder(lambda: format_time_ms(total()))  # v1.08


# ------------------------------------------------------------------ Schalter, Farbwahl, Bezeichnung (v1.11)

def title_without_flag(title):
    """'Zustände rotieren [0 / 1]' -> 'Zustände rotieren' (der Schalter zeigt den Wert)"""
    return re.sub(r"\s*\[\s*0\s*/\s*1\s*\]\s*$", "", str(title))


def single_target_title(title, keys):
    """Die Zielvariable heisst 'Zielvariable 1', auch wenn das Makro nur eine hat (DstVar1 ohne DstVar2/DstVarN): dann ohne die Ziffer"""
    if "DstVar1" in keys and not ({"DstVar2", "DstVarN"} & set(keys)):
        return re.sub(r"\s+1\s*$", "", str(title))
    return title


def parse_rgb(text, count):
    """'20 13 10' (oder mit Komma) -> Liste von count Zahlen 0..255; None, wenn die Anzahl nicht stimmt oder etwas keine Zahl ist"""
    parts = [x for x in re.split(r"[\s,;]+", str(text).strip()) if x != ""]
    if len(parts) != count:
        return None
    try:
        return [min(max(int(x), 0), 255) for x in parts]
    except ValueError:
        return None


def rgb_text(values):
    """[r, g, b, r, g, b] -> 'r g b  r g b' (wie bei RGB2 im Excel-Programm: zwei Leerzeichen zwischen den Farben)"""
    values = [int(v) for v in values]
    return "  ".join(" ".join(str(v) for v in values[i:i + 3]) for i in range(0, len(values), 3))


def _main_ctrl():
    """Steuerung des Programms (fuer den Mini-Farbtest); None, wenn nicht gefunden"""
    for name in ("__main__", "webmobaledlib"):
        c = getattr(sys.modules.get(name), "ctrl", None)
        if c is not None:
            return c
    return None


def _add_flag_row(ui, p, cur):
    """Wert 0 / 1 als Ein/Aus-Schalter. Rueckgabe: Holder mit '0' oder '1'."""
    with ui.row().classes("w-full items-center no-wrap gap-3"):
        ui.label(title_without_flag(p["title"])).classes("grow")
        sw = ui.switch(value=(parse_int(cur) or 0) != 0)
        shown = ui.label("1" if sw.value else "0").classes("text-grey-7 w-4 text-center")
    sw.on_value_change(lambda e: shown.set_text("1" if e.value else "0"))
    if p["tooltip"]:
        sw.tooltip(p["tooltip"])
    return _Holder(lambda: "1" if sw.value else "0")


def _add_rgb_row(ui, p, cur, count):
    """Farbe als Zahlen im Textfeld (nur so breit wie noetig, Experten aendern sie von Hand), Taste 'Farbe wählen' (Mini-Farbtest) und Felder mit der eingestellten Farbe.
    count: 3 (RGB) oder 6 (RGB2: zwei Farben im Wechsel). Rueckgabe: das Eingabefeld (value = Text der Zahlen)."""
    from _web.web_i18n import tr
    with ui.row().classes("w-full items-center no-wrap gap-3"):
        ui.label(p["title"]).classes("w-48 shrink-0")
        inp = ui.input(value=str(cur)).props("outlined dense").style("width: %dch; flex: none" % (14 if count == 3 else 24))
        button = ui.button(tr("Farbe wählen")).props("outline no-caps dense").classes("shrink-0")
        swatches = [ui.element("div").style("width: 44px; height: 32px; border: 1px solid #888; border-radius: 4px; flex: none") for _ in range(count // 3)]

    def show():
        vals = parse_rgb(inp.value, count)
        for i, sw in enumerate(swatches):
            if vals is None:
                sw.style("background: repeating-linear-gradient(45deg, #fff, #fff 4px, #ddd 4px, #ddd 8px)")
            else:
                sw.style("background: rgb(%d,%d,%d)" % tuple(vals[3 * i:3 * i + 3]))

    async def pick():
        from _web import web_colorcheck
        from _web.web_i18n import tr
        vals = parse_rgb(inp.value, count) or [0] * count
        names = [tr("Farbe (R, G, B)")] if count == 3 else [tr("Farbe 1 (R1, G1, B1)"), tr("Farbe 2 (R2, G2, B2)")]
        slots = [(names[i], tuple(vals[3 * i:3 * i + 3])) for i in range(count // 3)]
        ctrl = _main_ctrl()
        if ctrl is None:
            return
        # res = await web_colorcheck.open_mini(ctrl, None, title=tr("Mini-Farbtest"), slots=slots, passive=True)  # v1.13 (entfallen)
        res = await web_colorcheck.open_mini(ctrl, None, title=tr("Mini-Farbtest"), slots=slots, led=(0, 1, 0), passive=True)  # LED 0, Kanal 0: nur die Heartbeat-LED; die Nummer kann im Mini-Farbtest von Hand geaendert werden; gesendet wird erst bei einer Farbaenderung  # v1.13
        if res:
            inp.set_value(rgb_text([v for c in res for v in c]))
    inp.on_value_change(lambda _e: show())
    button.on_click(pick)
    show()
    if p["tooltip"]:
        inp.tooltip(p["tooltip"])
    return inp



LED_OPTION_COLORS = {"1": "#e0e0e0", "2": "#ffe44d", "3": "#4de8f0", "4": "#ff5c6e", "5": "#7ee07e", "6": "#6f8fff"}  # v1.10


def _add_led_buttons(ui, options, initial):  # v1.10
    """LED Kanal Auswahl als farbige Tasten (Gelb, Zyan, Rot, Gruen, Blau). Die gewaehlte Taste hat Rahmen und Fettschrift. Rueckgabe: Holder mit dem Wert."""  # v1.10
    state = {"v": initial if initial in options else options[0]}  # v1.10
    buttons = {}  # v1.10

    def style(v):  # v1.10
        sel = state["v"] == v  # v1.10
        return ("background-color: %s !important; color: #222 !important; opacity: %s; border: %s; font-weight: %s; min-width: 7em; text-transform: none;"  # v1.10
                % (LED_OPTION_COLORS.get(v, "#e0e0e0"), "1" if sel else "0.45", "3px solid #1976d2" if sel else "3px solid transparent", "bold" if sel else "normal"))  # v1.10

    def choose(v):  # v1.10
        state["v"] = v  # v1.10
        for k, b in buttons.items():  # v1.10
            b.style(replace=style(k))  # v1.10
    with ui.row().classes("w-full items-center gap-3"):  # v1.10
        for v in options:  # v1.10
            b = ui.button(LED_OPTION_LABELS[v], on_click=lambda _e, v=v: choose(v)).props("unelevated no-caps")  # v1.10
            b.style(replace=style(v))  # v1.10
            buttons[v] = b  # v1.10
    return _Holder(lambda: state["v"])  # v1.10


# ------------------------------------------------------------------ Dialog (Event-Loop)
async def _other_async(spec: dict, values: dict):
    from nicegui import ui
    inputs = {}
    with wd._bridge["client"]:
        with ui.dialog().props("persistent") as dlg, ui.card().classes("w-[820px] max-w-full"):
            ui.label(spec["title"]).classes("text-h6")
            ui.label(spec["description"]).classes("mll-desc").style(
                "white-space: pre-line; border: 1px solid #ccc; padding: 6px; width: 100%; max-height: 14em; overflow: auto")
            radio = chan = None
            if spec["led_options"]:
                ui.label("LED Kanal Auswahl").classes("text-bold")
                radio = _add_led_buttons(ui, spec["led_options"], values.get("option", spec["led_initial"]))  # v1.10
            if spec["channel"]:
                cval = values.get("channel", spec["channel"]["value"])  # v1.09
                if parse_int(cval) is not None:  # v1.09: Zahl: Feld wie die anderen Zahlenfelder
                    cnum = _stepper(ui, parse_int(cval), 0, 99999, 1, "w-36")  # v1.09
                    cnum.props("label=\"%s\"" % spec["channel"]["label"])  # v1.09
                    chan = _Holder(lambda: str(int(cnum.value or 0)))  # v1.09
                else:  # v1.09
                    chan = ui.input(label=spec["channel"]["label"], value=cval).props("outlined dense").classes("w-40")  # v1.09
            with ui.column().classes("w-full gap-1"):
                keys_all = [q["key"] for q in spec["params"]]  # v1.11
                for p in spec["params"]:
                    p = dict(p, title=single_target_title(p["title"], keys_all))  # v1.11: Zielvariable ohne die 1, wenn es nur eine gibt
                    cur = values.get("params", {}).get(p["key"], p["value"])
                    if p["type"] == "List":
                        opts = list(p["options"] or [])
                        if cur not in opts:
                            opts.append(cur)
                        w = ui.select(opts, value=cur, label=p["title"]).props("outlined dense").classes("w-full")
                    else:
                        # w = ui.input(label=p["title"], value=str(cur)).props("outlined dense").classes("w-full")  # v1.08 (entfallen)
                        w = None  # v1.08
                        if p.get("plain", True):  # v1.08: Optionen wie Inv oder pf veraendern den Wert: nur das Textfeld
                            if p["key"] == "HSVColor" and parse_int(cur) is not None:  # v1.08
                                w = _add_hue_row(ui, p, cur)  # v1.08
                            elif p.get("ptype") == "Time" and parse_time_ms(cur) is not None:  # v1.08
                                w = _add_time_row(ui, p, cur, parse_time_ms(cur))  # v1.08
                            elif p.get("ptype") in ("RGB", "RGB2") and parse_rgb(cur, 3 if p.get("ptype") == "RGB" else 6) is not None:  # v1.11
                                w = _add_rgb_row(ui, p, cur, 3 if p.get("ptype") == "RGB" else 6)  # v1.11
                            elif p.get("ptype") == "" and str(p.get("mn", "")).strip() == "0" and str(p.get("mx", "")).strip() == "1" and parse_int(cur) in (0, 1):  # v1.11
                                w = _add_flag_row(ui, p, cur)  # v1.11
                            elif p.get("ptype") == "" and slider_range(p.get("mn", ""), p.get("mx", ""), cur):  # v1.08
                                w = _add_number_row(ui, p, cur, slider_range(p.get("mn", ""), p.get("mx", ""), cur))  # v1.08
                        if w is None:  # v1.08
                            w = ui.input(label=p["title"], value=str(cur)).props("outlined dense").classes("w-full")  # v1.08
                            if p["tooltip"]:  # v1.08
                                w.tooltip(p["tooltip"])  # v1.08
                        inputs[p["key"]] = w  # v1.08
                        continue  # v1.08
                    if p["tooltip"]:
                        w.tooltip(p["tooltip"])
                    inputs[p["key"]] = w

            def collect():
                return {"params": {k: w.value for k, w in inputs.items()},
                        "option": radio.value if radio else None,
                        "channel": chan.value if chan else None}

            with ui.row().classes("justify-end w-full"):
                ui.button("Abbrechen", on_click=lambda: dlg.submit((None, None))).props("flat").classes("mll-cancel")
                if spec["patch"]:
                    ui.button("Patch", on_click=lambda: dlg.submit(("patch", collect()))).props("outline")
                ui.button("Ok", on_click=lambda: dlg.submit(("ok", collect()))).classes("mll-default")
        res = await dlg
        wd.safe_delete(dlg)
    return res


# ------------------------------------------------------------------ Klasse erzeugen
def make_class(Base):
    ns = sys.modules[Base.__module__].__dict__
    Split, Trim, Left, Len, Mid, Replace, InStr, UBound = (ns[n] for n in
        ("Split", "Trim", "Left", "Len", "Mid", "Replace", "InStr", "UBound"))
    M09, M10, M25, M30, P01 = (ns[n] for n in ("M09", "M10", "M25", "M30", "P01"))
    vbCritical = ns["vbCritical"]

    class WebUserFormOther(Base):
        def Show_UserForm_Other(self, Par, Name, Description, LedChannels, Show_Channel, LED_Channel,
                                Def_Channel, CV_Adress=None, CV_used=None):
            if not wd.bridge_usable():
                return super().Show_UserForm_Other(Par, Name, Description, LedChannels, Show_Channel,
                                                   LED_Channel, Def_Channel, CV_Adress=CV_Adress, CV_used=CV_used)
            self.UserForm_Res = ""
            self.title = M09.Get_Language_Str("Parametereingabe der '") + Name + M09.Get_Language_Str("' Funktion")
            self.FuncName = Name
            self.Show_Channel_Type = Show_Channel
            if Description == "":
                Description = (M09.Get_Language_Str("Noch keine Beschreibung zur Funktion '") + Name
                               + M09.Get_Language_Str("' vorhanden ;-("))
            self.ParList = Split(Par, ",")
            uses_cx = M30.Is_Contained_in_Array("Cx", self.ParList) or M30.Is_Contained_in_Array("B_LED_Cx", self.ParList)

            led_options = available_led_options(LedChannels) if uses_cx else None
            led_initial = led_options[0] if led_options else "1"

            OldCmdLine = P01.Cells(P01.ActiveCell().Row, M25.Config__Col)
            UseOldParams = False
            OldParams = None
            if Len(OldCmdLine) > Len(Name) and Left(OldCmdLine, Len(Name) + 1) == Name + "(":
                UseOldParams = True
                OldParams = Split(Trim(Replace(Mid(OldCmdLine, Len(Name) + 2), ")", "")), ",")

            channel = None
            if Show_Channel != M10.CHAN_TYPE_NONE:
                channel = {"label": "LED Channel", "value": "1"}
                if Show_Channel == M10.CHAN_TYPE_SERIAL:
                    channel = {"label": M09.Get_Language_Str("Sound Kanal"), "value": str(LED_Channel)}
                elif Show_Channel == M10.CHAN_TYPE_LED:
                    channel["value"] = str(LED_Channel if UseOldParams else Def_Channel)

            params = []
            self.ParamVar = {}
            Nr = 0
            UsedParNr = 0
            for p in self.ParList:
                p = Trim(p)
                if Left(p, 1) != "#" and InStr(" Cx B_LED_Cx ", " " + p + " ") == 0:
                    if UsedParNr >= self.MAX_PAR_CNT:
                        P01.MsgBox("Internal error: The number of parameters is to large in Show_UserForm_Other()",
                                   vbCritical, "Internal Error")
                        M30.EndProg()
                    ParVal = ""
                    Typ, Min, Max, Def, Opt, InpTxt, Hint = M10.Get_Par_Data(p)
                    if UseOldParams:
                        if Typ == "RGB":
                            # ParVal = self.Get_RGB_from_OldParams(OldParams, Nr, 3)  # v1.06 (entfallen)
                            if Nr + 2 <= UBound(OldParams):                         # nur wenn die drei Werte in der Zelle stehen (sonst Vorgabe, zum Beispiel bei "Name(" aus der Grafik)  # v1.06
                                ParVal = self.Get_RGB_from_OldParams(OldParams, Nr, 3)  # v1.06
                            Nr = Nr + 2
                        elif Typ == "RGB2":
                            # ParVal = (self.Get_RGB_from_OldParams(OldParams, Nr, 3) + "  "  # v1.06 (entfallen)
                                      # + self.Get_RGB_from_OldParams(OldParams, Nr + 3, 3))  # v1.06 (entfallen)
                            if Nr + 5 <= UBound(OldParams):  # v1.06
                                ParVal = (self.Get_RGB_from_OldParams(OldParams, Nr, 3) + "  "  # v1.06
                                          + self.Get_RGB_from_OldParams(OldParams, Nr + 3, 3))  # v1.06
                            Nr = Nr + 5
                        else:
                            if Nr <= UBound(OldParams):
                                ParVal = OldParams(Nr)
                    ParVal = Trim(ParVal)
                    self.Prefix[UsedParNr] = ''                                                       # Version K  # v1.04
                    self.TypA[UsedParNr] = Typ
                    self.MinA[UsedParNr] = Min
                    self.MaxA[UsedParNr] = Max
                    self.ParName[UsedParNr] = p
                    UsedParNr = UsedParNr + 1
                    SelectValues = None
                    plain = True                                                                # v1.08: False bei den Optionen Inv, pf und ... (Wert wird veraendert): nur Textfeld
                    if norm(Opt) != "":
                        for OptionValue in Split(Opt, ";"):
                            OptionValue = Trim(OptionValue)
                            if OptionValue.lower().startswith("values:"):
                                SelectValues = Trim(Mid(OptionValue, 8)).split(",")
                            else:
                                for o in Split(OptionValue, " "):
                                    Parts = Split(o, "=")
                                    key = Parts(0)
                                    if key in ("w", "wn"):
                                        pass                         # Breite: im Web nicht noetig
                                    elif key == "Inv":
                                        plain = False  # v1.08
                                        self.Invers[UsedParNr - 1] = True
                                        ParVal = 1 if ParVal == 0 else 0
                                    elif key == "pf":                                        # Version K: Praefix fuer das Argument (08.12.25: Juergen)  # v1.04
                                        plain = False  # v1.08
                                        self.Prefix[UsedParNr - 1] = Parts(1)  # v1.04
                                        import proggen.Userform_Other as D07_pf                                        # Version K  # v1.04
                                        ParVal = D07_pf.ValToParVal(Parts(1), ParVal)  # v1.04
                                    elif key in ("...", "…"):
                                        plain = False  # v1.08
                                        if UseOldParams:
                                            for i in range(UsedParNr + 1, UBound(OldParams) + 1):
                                                ParVal = ParVal + ", " + Trim(OldParams(i))
                                    else:
                                        P01.MsgBox("Internal Error: Unknown option '" + o + "' in parameter '"
                                                   + str(norm(InpTxt)) + "'", vbCritical, "Internal Error")
                                        M30.EndProg()
                    validListEntry = False
                    if SelectValues:
                        for SelectValue in SelectValues:
                            SelectValue = Trim(SelectValue)
                            if SelectValue != "" and SelectValue == ParVal:
                                validListEntry = True
                    if ParVal == "":
                        ParVal = Def
                        validListEntry = True
                    # if Typ == "List" or Typ == "Mode":  # v1.07 (entfallen)
                    if Typ == "List":  # v1.07: Mode hat keine feste Auswahl (OptCtrPar: Flags und Zahlen)
                        if not validListEntry:
                            P01.MsgBox(Replace(Replace(Replace(M09.Get_Language_Str(
                                "Fehler: Der Parameter '#1#' hat einen ungültigen Wert #2#. Der Parameter wird auf den "
                                "Standardwert #3# zurückgesetzt."), "#1#", p), "#2#", ParVal), "#3#", Def),
                                vbCritical, M09.Get_Language_Str("Ungültiger Parameter"))
                            ParVal = Def
                    self.Controls["Par" + str(UsedParNr)] = ParVal
                    self.Controls["LabelPar" + str(UsedParNr)] = str(norm(InpTxt))
                    wtype = MLL_TYPE_TO_WIDGET.get(str(norm(Typ)), "String")
                    params.append({"key": p, "title": str(norm(InpTxt)), "tooltip": str(norm(Hint)),
                                   "type": wtype, "options": [Trim(s) for s in (SelectValues or []) if Trim(s) != ""],
                                   "value": "" if norm(ParVal) == "" else str(norm(ParVal)),
                                   "ptype": str(norm(Typ)), "mn": str(norm(Min)), "mx": str(norm(Max)), "plain": plain})  # v1.08
                if p == "Cx" or p == "B_LED_Cx":
                    # if UseOldParams:  # v1.05 (entfallen)
                    if UseOldParams and Nr <= UBound(OldParams):                  # steht in der Zelle nur der Makroname ("Name(", zum Beispiel aus der Grafik) oder weniger Parameter: Vorgabe nehmen  # v1.05
                        v = option_value_for(Trim(OldParams(Nr)), p == "B_LED_Cx")
                        if v is None:
                            P01.MsgBox(M09.Get_Language_Str("Fehler beim Lesen der bestehenden Kanalbezeichnung '")
                                       + Trim(OldParams(Nr)) + "'", vbCritical,
                                       M09.Get_Language_Str("Unbekannte Kanalbezeichnung"))
                        else:
                            led_initial = v
                Nr = Nr + 1

            for q_nr, q in enumerate(params):  # v1.12: Bezeichnung 'Zielvariable' ohne die 1 auch in den Fehlermeldungen
                q_old = q["title"]  # v1.14
                q["title"] = single_target_title(q["title"], [x["key"] for x in params])  # v1.12
                if q["title"] != q_old and q["key"] == "DstVar1":  # v1.14: nur eine Zielvariable: Hinweis auf die Namen der weiteren Zustaende
                    from _web.web_i18n import tr  # v1.14
                    q["tooltip"] = (str(q["tooltip"]) + "\n" if q["tooltip"] else "") + tr("Hier wird der Name für den Zustand 0 eingegeben, zum Beispiel Test0. Die Variablen für die weiteren Zustände heißen dann Test1, Test2, … (Zielvariable 1, 2, … in der Beschreibung).")  # v1.14
            for q_nr, q in enumerate(params, 1):  # v1.12
                if "LabelPar" + str(q_nr) in self.Controls:  # v1.12
                    self.Controls["LabelPar" + str(q_nr)] = q["title"]  # v1.12
            self.CV_Adress = CV_Adress
            self.CV_Used = CV_used
            spec = {"title": self.title, "description": str(Description), "led_options": led_options,
                    "led_initial": led_initial, "channel": channel, "params": params,
                    "patch": CV_Adress is not None and CV_Adress != 0}
            values: dict = {}
            while True:
                action, vals = wd.call_in_loop(_other_async, spec, values, default=(None, None))
                if action is None:
                    self.UserForm_Res = "<Abort>"
                    break
                values = vals
                self._apply_values(vals)
                if action == "patch":
                    try:
                        self.patch_cmd()
                    except Exception as ex:                       # noqa: BLE001
                        logger.exception("Patch fehlgeschlagen")
                        P01.MsgBox("Patch fehlgeschlagen: " + str(ex), vbCritical, "Patch")
                    continue
                res = self.Create_Result()                         # Pruefungen des Originals
                if res:
                    self.UserForm_Res = res
                    break
                # ungueltige Eingabe: Meldung wurde angezeigt, Dialog bleibt mit den Eingaben offen
            P01.ActiveSheet.Redraw_table()

        def _apply_values(self, vals):
            """Werte des Dialogs in die Variablen schreiben, die Create_Result/Check_* lesen."""
            for i in range(self.MAX_PAR_CNT):
                name = self.ParName[i]
                if name in vals["params"]:
                    self.ParamVar[name] = Var(vals["params"][name])
                    self.Controls["Par" + str(i + 1)] = vals["params"][name]
            self.RB_Option_Button_var = Var(vals["option"] if vals["option"] is not None else "1")
            self.LED_Channel_TextBox_svar = Var(vals["channel"]) if vals["channel"] is not None else None

    WebUserFormOther.__name__ = "WebUserFormOther"
    return WebUserFormOther


def install():
    import proggen.Userform_Other as D07
    if getattr(D07.UserForm_Other, "__name__", "") != "WebUserFormOther":
        D07.UserForm_Other = make_class(D07.UserForm_Other)
        logger.info("Web-Parameterformular installiert (UserForm_Other)")
