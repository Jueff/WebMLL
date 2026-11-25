# Datei-Version: 1.17 (2026-11-25) - web_form_comport.py
# ----------------------------------------------------------------------------------------------
# Name:           web_form_comport.py
# Path:           _web/web_form_comport.py
# Version:        1.17
# Last Update:    2026-11-25
# Author:         Harold Linke, Jürgen Winkler
# Licence:        LGPL V2.1
# History of Change:
#   1.17  2026-11-25  Korrektur zu 1.16: Name des Anschlusses steht wieder in der Liste; entfallen ist nur die Statuszeile ueber der Liste (Name des gewaehlten Anschlusses).
#                     Fehlermeldungen (z. B. 'Kein COM Port erkannt') erscheinen weiter. Zeilen mit '# v1.17'
#   1.16  2026-11-25  Geräteauswahl: einleitender Satz ('Es wird der COM Port überprüft ...') und Name des Anschlusses (z. B. 'Silicon Labs CP210x ...') entfallen,
#                     Liste doppelt so hoch (520 px), Typabfrage mit OK links und Abbrechen rechts (mll-default/mll-cancel). Zeilen mit '# v1.16'
#   1.15  2026-11-25  Weitere Texte: 'OK, wenn die LEDs am richtigen Gerät schnell blinken.', 'Kein Gerät gefunden. Bitte das Gerät per USB anschließen.' Zeilen mit '# v1.15'
#   1.14  2026-11-25  Texte des Dialogs der Lichtmaschine: 'an dem die Lichtmaschine angeschlossen ist', 'Gefundene Geräte', Hinweis zur Liste (statt Pfeiltasten);
#                     roter Hinweis 'Tipp: Der ausgewählte Arduino blinkt schnell' entfernt. Zeilen mit '# v1.14'
#   1.13  2026-11-25  Protokoll und Board-Variante wieder aus dem Dialog entfernt: sie stehen jetzt auf der Hauptseite (Optionen, Reiter Lichtmaschine); der Dialog ist nur noch die Auswahlliste
#   1.12  2026-11-25  (v1.13 entfallen) Board-Variante (Nano alt/neu/Full, Uno) im unteren Bereich des Dialogs (kommt aus dem Reiter Lichtmaschine der Optionen); find_image() auf Modulebene
#   1.11  2026-11-25  Dialog der Lichtmaschine neu (Zeilen mit '# v1.11'): Liste aller gefundenen Boards gruppiert nach Classic / Pro / Pico mit Typ und Anschluss; das im Blatt
#                     eingestellte Board steht immer drin (offline, wenn es nicht am USB haengt); 'Unbekannte Ports' (Vorgabe aus) fuegt die Gruppe 'unbekannt' hinzu, beim OK
#                     wird der Typ abgefragt; Bild rechts folgt der Auswahl.
#                     Die anderen Dialoge (rechter Arduino, ISP, WLAN) bleiben unveraendert.
#   1.02  2026-10-15  Web-Ersatz fuer Select_COM_Port_Userform (Original, nicht erfasst)
#   1.09  2026-11-22  Issue 37: nach dem Wechsel des Boards ueber 'Andere Typen' werden Bild, Beschreibungstext und roter Hinweis des Dialogs neu gesetzt
#   1.08  2026-11-19  Bilddatei unabhaengig von Gross- und Kleinschreibung suchen (LED_Image heisst LED_image.png: unter Linux und auf dem Pi fehlte das Bild; Issue 27, Juergen)
#   1.07  2026-11-14  'Andere Typen' anklickbar: Rueckfrage, Typwechsel (zuletzt benutzte Variante), Anschluss waehlen; Abbrechen stellt den alten Typ wieder her
#   1.06  2026-11-14  Zeile 'Andere Typen: COM3(ESP32), COM5(Pico)' wie in Excel
#   1.03  2026-10-21  Update_SpinButton: ohne offenen Dialog den Zeitgeber der blinkenden LEDs beenden (stand 10 Minuten lang auf COM6 und blockierte esptool)
#   1.04  2026-10-26  Unbekannte Ports anzeigen ist unter Linux und macOS nur noch an, wenn kein bekannter Anschluss (zum Beispiel ttyUSB0) gefunden wird
#   1.05  2026-10-28  neu angeschlossenes Geraet wird gewaehlt (0 = keine Vorgabe, Anschluss am Ende der Liste); Protokollzeile bei Aenderung der Anschlussliste
#   1.10  2026-11-23  Identify (Juergen Winkler): ESP32/Pico: beim Wechsel des Anschlusses '~MLLIDENT 0' an den alten und '~MLLIDENT 1' an den neuen Anschluss, '~MLLIDENT 0' beim Schliessen
#                     des Dialogs und wenn kein Anschluss mehr da ist (_old_comport). Zeilen mit '# v1.10'
# ----------------------------------------------------------------------------------------------
"""Web-Ersatz fuer proggen/Select_COM_Port_Userform.py (Auswahl des Arduino/Pico-Ports).

WebSelectComPort erbt von CSelect_COM_Port_UserForm und ersetzt ShowDialog, Update_SpinButton und
Show_Status. Wichtig ist das Zusammenspiel mit M07: Waehrend der Dialog offen ist, ruft ein Zeitgeber
(__Blink_Arduino_LED) jede Sekunde Update_SpinButton() und Show_Status() auf, um die Liste der Ports und
die Statusmeldung zu aktualisieren und die LEDs des gewaehlten Arduinos blinken zu lassen. Diese
Aufrufe kommen aus einem Hintergrund-Thread und werden hier per call_soon_threadsafe in den Browser
uebertragen.

Die Hinweistexte werden aus dem Quelltext des Originals gelesen (ast).
"""
from __future__ import annotations

import ast
import inspect
import logging
import os
import sys
import textwrap

from _web import web_dialogs as wd

logger = logging.getLogger(__name__)


def harvest_hints(Base) -> dict:
    """Hint_Label_text-Zuweisungen (Linux/Mac, Windows, WLAN) und Text des Kontrollkaestchens."""
    out = {"hints": [], "unknown": None}
    src = textwrap.dedent(inspect.getsource(Base.ShowDialog))
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Attribute) \
                and node.targets[0].attr == "Hint_Label_text":
            call = node.value
            if isinstance(call, ast.Call) and call.args and isinstance(call.args[0], ast.Constant):
                out["hints"].append(call.args[0].value)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "Checkbutton":
            for kw in node.keywords:
                if kw.arg == "text" and isinstance(kw.value, ast.Call) and kw.value.args \
                        and isinstance(kw.value.args[0], ast.Constant):
                    out["unknown"] = kw.value.args[0].value
    out["hints"].sort(key=lambda s: 0)           # Reihenfolge des Quelltextes beibehalten
    return out


def split_buttons(buttons: str) -> list[tuple[int, str]]:
    """'H Hallo; A Abbruch; O Ok' -> [(1, 'Hallo'), (2, 'Abbruch'), (3, 'Ok')]; leere Eintraege entfallen."""
    res = []
    for i, b in enumerate(buttons.split(";"), start=1):
        b = b.strip()
        if len(b) >= 3 and b[1] == " ":
            res.append((i, b[2:]))
    return res


def find_image(picture: str) -> str:  # v1.12: Web-Pfad der Bilddatei (ohne Beachtung der Gross-/Kleinschreibung), "" wenn es sie nicht gibt
    try:
        folder = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "images")
        wanted = (picture + ".png").lower()
        found = next((f for f in os.listdir(folder) if f.lower() == wanted), None)
    except OSError:
        found = None
    return "/mll_images/" + found if found else ""


# ------------------------------------------------------------------ Dialog (Event-Loop)
async def _comport_async(form, spec):
    from nicegui import ui
    with wd._bridge["client"]:
        with ui.dialog().props("persistent") as dlg, ui.card().classes("w-[900px] max-w-full"):
            with ui.row().classes("no-wrap w-full items-start"):
                with ui.column().classes("grow gap-2"):
                    ui.label(spec["title"]).classes("text-h6")
                    # ui.label(spec["text"]).style("white-space: pre-line")  # v1.09 (entfallen)
                    text_lbl = ui.label(spec["text"]).style("white-space: pre-line")  # v1.09: Referenz fuer den Boardwechsel
                    status = ui.label("").classes("text-grey-8").style("white-space: pre-line")
                    error = ui.label("").classes("text-red-8 text-bold").style("white-space: pre-line")
                    error.set_visibility(False)
                    sel = chk = avail = other_box = None  # v1.07
                    if spec["show_port"]:
                        sel = ui.select(spec["ports"], value=spec["port"], label="COM Port").props("outlined dense").classes("w-80")
                        chk = ui.checkbox(spec["unknown_text"], value=spec["show_unknown"])
                        avail = ui.label(spec["avail"]).classes("text-caption").style("white-space: pre-line")
                        other_box = ui.row().classes("items-center gap-1 text-caption")  # v1.07: Andere Typen, anklickbar
                        ui.label(spec["hint"]).style("white-space: pre-line")
                with ui.column().classes("items-end gap-2").style("min-width: 200px"):
                    # if spec["red_hint"]:  # v1.09 (entfallen)
                    #     ui.label(spec["red_hint"]).classes("text-red-8").style("white-space: pre-line")  # v1.09 (entfallen)
                    # if spec["image"]:  # v1.09 (entfallen)
                    #     ui.image(spec["image"]).classes("w-48")  # v1.09 (entfallen)
                    red_lbl = ui.label(spec["red_hint"] or "").classes("text-red-8").style("white-space: pre-line")  # v1.09: immer anlegen, damit der Boardwechsel sie aendern kann
                    red_lbl.set_visibility(bool(spec["red_hint"]))  # v1.09
                    img = ui.image(spec["image"] or "").classes("w-48")  # v1.09
                    img.set_visibility(bool(spec["image"]))  # v1.09
            with ui.row().classes("justify-end w-full"):
                for n, text in spec["buttons"]:
                    ui.button(text, on_click=lambda n=n: dlg.submit(n)).props("" if n == 3 else "outline").classes(
                        "mll-default" if n == 3 else ("mll-cancel" if n == 2 else ""))

            if sel is not None:
                def on_sel(e):
                    form._sel_index = spec_ports()[0].index(e.value) if e.value in spec_ports()[0] else form._sel_index
                sel.on_value_change(on_sel)
                chk.on_value_change(lambda e: setattr(form, "_show_unknown", bool(e.value)))

            def spec_ports():
                return (list(sel.options) if sel is not None else [],)

            async def on_pick(dev, typ):  # v1.07: Klick auf einen Anschluss anderen Typs: nachfragen, Typ wechseln, Anschluss waehlen
                with wd._bridge["client"]:
                    with ui.dialog().props("persistent") as d, ui.card():
                        ui.label(spec["switch_text"].replace("%1", typ).replace("%2", dev)).style("white-space: pre-line")
                        with ui.row().classes("justify-end w-full"):
                            ui.button(spec["no_text"], on_click=lambda: d.submit(False)).props("outline")
                            ui.button(spec["yes_text"], on_click=lambda: d.submit(True))
                    yes = await d
                    wd.safe_delete(d)
                if yes and form._switch_type(typ):
                    ports_, port_, avail_ = form._compute(dev)
                    sel.set_options(ports_, value=dev if dev in ports_ else (port_ if port_ in ports_ else None))
                    avail.set_text(avail_)
                    render_other()
                    if spec.get("main_col"):  # v1.09: Issue 37: Bild, Text und roter Hinweis zum neuen Board
                        try:  # v1.09
                            view = form._board_view()  # v1.09
                            text_lbl.set_text(view["text"])  # v1.09
                            red_lbl.set_text(view["red_hint"])  # v1.09
                            red_lbl.set_visibility(bool(view["red_hint"]))  # v1.09
                            img.set_source(view["image"])  # v1.09
                            img.set_visibility(bool(view["image"]))  # v1.09
                        except Exception:                                   # noqa: BLE001  # v1.09
                            logger.exception("Port-Auswahl: Anzeige nach dem Boardwechsel nicht aktualisiert")  # v1.09

            def render_other():  # v1.07
                if other_box is None:
                    return
                other_box.clear()
                items = getattr(form, "_other", [])
                if not items:
                    return
                with other_box:
                    ui.label(spec["other_text"])
                    for dev, typ in items:
                        ui.button("%s(%s)" % (dev, typ), on_click=lambda dev=dev, typ=typ: on_pick(dev, typ)).props("flat dense no-caps size=sm color=primary")

            render_other()
            form._ui = {"loop": wd._bridge["loop"], "status": status, "error": error, "select": sel, "avail": avail, "render_other": render_other}
            form.isInitialised = True
        res = await dlg
        form.isInitialised = False
        form._ui = None
        wd.safe_delete(dlg)
    return res


# ------------------------------------------------------------------ neuer Dialog der Lichtmaschine (v1.11)
async def _comport_async_new(form, spec):  # v1.11
    from nicegui import ui
    with wd._bridge["client"]:
        with ui.dialog().props("persistent") as dlg, ui.card().classes("w-[900px] max-w-full"):
            ui.label(spec["title"]).classes("text-h6")
            # ---- oberer Bereich: Liste der Boards links, Bild rechts
            with ui.row().classes("no-wrap w-full items-start"):
                with ui.column().classes("grow gap-2"):
                    text_lbl = ui.label(spec["text"]).style("white-space: pre-line")
                    text_lbl.set_visibility(bool(spec["text"]))  # v1.16: ohne Text keine leere Zeile
                    status = ui.label("").classes("text-grey-8").style("white-space: pre-line")
                    status.set_visibility(False)  # v1.17: keine Statuszeile (Name des Anschlusses steht in der Liste)
                    error = ui.label("").classes("text-red-8 text-bold").style("white-space: pre-line")
                    error.set_visibility(False)
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(spec["list_title"]).classes("text-subtitle2")
                        chk = ui.checkbox(spec["unknown_text"], value=False)
                    # list_box = ui.column().classes("w-full gap-0 border rounded").style("max-height: 260px; overflow-y: auto")  # v1.16 (entfallen)
                    list_box = ui.column().classes("w-full gap-0 border rounded").style("max-height: 520px; overflow-y: auto")  # v1.16: Liste doppelt so hoch
                    if spec["hint"]:
                        ui.label(spec["hint"]).classes("text-caption").style("white-space: pre-line")
                with ui.column().classes("items-end gap-2").style("min-width: 200px"):
                    red_lbl = ui.label(spec["red_hint"] or "").classes("text-red-8").style("white-space: pre-line")
                    red_lbl.set_visibility(bool(spec["red_hint"]))
                    img = ui.image(spec["image"] or "").classes("w-48")
                    img.set_visibility(bool(spec["image"]))

            sig = [None]

            def render_list():
                rows, sel = form._rows, form._sel_dev
                s = (tuple((r["typ"], r["dev"], r["offline"]) for r in rows), sel)
                if s == sig[0]:
                    return
                sig[0] = s
                list_box.clear()
                with list_box:
                    if not rows:
                        ui.label(spec["none_text"]).classes("text-grey-7 q-pa-sm")
                        return
                    with ui.row().classes("w-full items-center no-wrap px-2 text-caption text-grey-7"):
                        ui.label("").classes("w-6")
                        ui.label(spec["col_type"]).classes("w-24")
                        ui.label(spec["col_port"])
                    last = None
                    for r in rows:
                        if r["typ"] != last:
                            last = r["typ"]
                            ui.label(spec["groups"].get(last, last)).classes("w-full px-2 py-1 text-bold bg-grey-2")
                        selected = r["dev"] == sel
                        row = ui.row().classes("w-full items-center no-wrap px-2 py-1 cursor-pointer" + (" bg-blue-1" if selected else ""))
                        row.on("click", lambda dev=r["dev"]: on_select(dev))
                        with row:
                            ui.icon("radio_button_checked" if selected else "radio_button_unchecked").classes("w-6 text-primary")
                            ui.label(spec["types"].get(r["typ"], r["typ"])).classes("w-24")
                            ui.label(r["dev"]).classes("text-bold").style("min-width: 110px")
                            if r["offline"]:
                                ui.badge(spec["offline_text"]).props("color=grey-7")
                            # else:  # v1.16 (entfallen: Name des Anschlusses, z. B. 'Silicon Labs CP210x USB to UART Bridge (COM3)', wird nicht mehr angezeigt)
                            #     ui.label(r["desc"]).classes("text-caption text-grey-7")  # v1.16 (entfallen)
                            else:  # v1.17: der Name des Anschlusses steht wieder in der Liste (nur die Statuszeile darueber entfaellt)
                                ui.label(r["desc"]).classes("text-caption text-grey-7")  # v1.17

            def refresh_view():  # Bild, Text und roter Hinweis zum aktuellen Board
                try:
                    view = form._board_view()
                    text_lbl.set_text(view["text"])
                    text_lbl.set_visibility(bool(view["text"]))  # v1.16
                    red_lbl.set_text(view["red_hint"])
                    red_lbl.set_visibility(bool(view["red_hint"]))
                    img.set_source(view["image"])
                    img.set_visibility(bool(view["image"]))
                except Exception:                                           # noqa: BLE001
                    logger.exception("Port-Auswahl: Anzeige nach dem Boardwechsel nicht aktualisiert")

            def on_select(dev):
                form._sel_dev = dev
                row = form._row(dev)
                if row and row["typ"] in form._GROUPS and row["typ"] != form._sheet_group():
                    if form._apply_group(row["typ"]):
                        refresh_view()
                form._compute_new()                                         # Ident und Blinken folgen sofort der Auswahl
                render_list()

            def on_unknown(e):
                form._show_unknown = bool(e.value)
                form._compute_new()
                render_list()

            async def ask_type(dev):  # Typ eines unbekannten Anschlusses abfragen; None = Abbruch
                with wd._bridge["client"]:
                    with ui.dialog().props("persistent") as d, ui.card():
                        ui.label(spec["ask_text"].replace("%1", dev)).style("white-space: pre-line")
                        radio = ui.radio(spec["ask_options"], value="Classic")
                        with ui.row().classes("justify-end w-full"):
                            # ui.button(spec["no_text"], on_click=lambda: d.submit(None)).props("outline")  # v1.16 (entfallen)
                            # ui.button("OK", on_click=lambda: d.submit(radio.value))  # v1.16 (entfallen)
                            ui.button("OK", on_click=lambda: d.submit(radio.value)).classes("mll-default")  # v1.16: OK links (Enter)
                            ui.button(spec["no_text"], on_click=lambda: d.submit(None)).props("outline").classes("mll-cancel")  # v1.16: Abbrechen rechts (Esc), wie in allen Dialogen
                    typ = await d
                    wd.safe_delete(d)
                return typ

            async def on_ok():
                row = form._row(form._sel_dev)
                if row and row["typ"] == "unbekannt":
                    typ = await ask_type(row["dev"])
                    if typ is None:
                        return                                              # Dialog bleibt offen
                    if form._apply_group(typ):
                        refresh_view()
                    row["typ"] = typ
                elif row and row["typ"] in form._GROUPS and row["typ"] != form._sheet_group():
                    form._apply_group(row["typ"])                           # Vorauswahl einer anderen Gruppe ohne Klick
                dlg.submit(3)

            chk.on_value_change(on_unknown)
            with ui.row().classes("justify-end w-full"):
                for n, text in spec["buttons"]:
                    if n == 3:
                        ui.button(text, on_click=on_ok).classes("mll-default")
                    else:
                        ui.button(text, on_click=lambda n=n: dlg.submit(n)).props("outline").classes("mll-cancel" if n == 2 else "")

            render_list()
            form._ui = {"loop": wd._bridge["loop"], "status": status, "error": error, "select": None, "render_list": render_list}
            form.isInitialised = True
        res = await dlg
        form.isInitialised = False
        form._ui = None
        wd.safe_delete(dlg)
    return res


# ------------------------------------------------------------------ Klasse
def make_class(Base):
    ns = sys.modules[Base.__module__].__dict__
    M07, M09, M30, M02, M25, P01 = (ns[n] for n in ("M07", "M09", "M30", "M02", "M25", "P01"))
    vbCritical, vbCr, InStr = ns["vbCritical"], ns["vbCr"], ns["InStr"]
    info = harvest_hints(Base)
    here = os.path.dirname(os.path.dirname(os.path.realpath(sys.modules[Base.__module__].__file__)))

    class WebSelectComPort(Base):
        _ui = None
        _sel_index = -1
        _old_spin = -1
        _show_unknown = False
        _old_comport = None  # Vorherig gewaehlter COM Port fuer Ident_Stop/Ident_Start beim Wechsel  # v1.10

        def _initial_show_unknown(self, windows):  # v1.04
            """Vorgabe fuer "Unbekannte Ports anzeigen": Windows aus; Linux und macOS nur dann an, wenn kein bekannter Anschluss gefunden wird (sonst standen unter Linux
            immer alle Anschluesse in der Liste und der letzte wurde vorgeschlagen, zum Beispiel ttyS31 statt ttyUSB0)"""
            if windows:  # v1.04
                return False  # v1.04
            try:  # v1.04
                known, _names = M07.EnumComPorts(False, [], PrintDebug=False)  # v1.04
                return len(known) == 0  # v1.04
            except Exception:                                              # noqa: BLE001  # v1.04
                logger.debug("Anschluesse konnten nicht gelesen werden", exc_info=True)  # v1.04
                return True  # v1.04

        # ------------------------------------------------------------ Typwechsel (v1.07)
        _VARIANTS = {}                                                      # Typ -> zuletzt benutzte Build-Optionen (ohne WLAN-Varianten), gilt bis zum Neustart

        def _read_buildopt(self):  # v1.07
            v = P01.Cells(M02.SH_VARS_ROW, M25.BUILDOP_COL).Value
            return "" if v is None else str(v)

        def _write_buildopt(self, text):  # v1.07
            P01.CellDict[M02.SH_VARS_ROW, M25.BUILDOP_COL] = text

        def _remember_variant(self, buildopt):  # v1.07
            if "WLAN" in buildopt:
                return
            if "rp2040" in buildopt:
                typ = "Pico"
            elif "esp32" in buildopt:
                typ = "ESP32"
            else:
                for b in (M02.BOARD_NANO_OLD, M02.BOARD_NANO_FULL, M02.BOARD_NANO_NEW, M02.BOARD_UNO_NORM):
                    if b in buildopt:
                        WebSelectComPort._VARIANTS["Nano"] = b               # nur der Board-Teil, weitere Optionen bleiben beim Wechsel erhalten
                        break
                return
            WebSelectComPort._VARIANTS[typ] = buildopt.replace(M02.AUTODETECT_STR, "").strip()

        def _find_image(self, picture):  # v1.09: Bilddatei ohne Beachtung der Gross-/Kleinschreibung suchen (wie in ShowDialog)
            try:  # v1.09
                wanted = (picture + ".png").lower()  # v1.09
                found = next((f for f in os.listdir(os.path.join(here, "images")) if f.lower() == wanted), None)  # v1.09
            except OSError:  # v1.09
                found = None  # v1.09
            return "/mll_images/" + found if found else ""  # v1.09

        def _board_view(self):  # v1.09: Bild, Beschreibungstext und roter Hinweis fuer das aktuell eingestellte Board (wie M07_COM_Port_New.Show_USB_Port_Dialog)
            import proggen.M02a_Public as M02a  # v1.09
            import proggen.M08_ARDUINO as M08  # v1.09
            is_arduino = True  # v1.09
            if M02a.Get_BoardTyp() == M02.HT_ESP32:  # v1.09
                picture, is_arduino = "ESP32_Image", False  # v1.09
                M08.SetArduName()  # v1.09
            elif M02a.Get_BoardTyp() == M02.HT_PICO:  # v1.09
                picture, is_arduino = "PICO_Image", False  # v1.09
                M08.SetArduName()  # v1.09
            elif InStr(P01.Cells(M02.SH_VARS_ROW, M25.BUILDOP_COL), "WLAN") > 0:  # v1.09
                picture, is_arduino = "PICOWL_Image", False  # v1.09
                M08.SetArduName("PICOWL")  # v1.09
            else:  # v1.09
                picture = "LED_Image"  # v1.09
                M08.SetArduName("LED")  # v1.09
            # text = M09.Get_Language_Str("Es wird der COM Port überprüft bzw. ausgewählt, an den der #1# angeschlossen ist.").replace("#1#", M08.GetArduName())  # v1.09  # v1.14 (entfallen)
            # text = M09.Get_Language_Str("Es wird der COM Port überprüft bzw. ausgewählt, an dem die Lichtmaschine angeschlossen ist.")  # v1.14: Lichtmaschine statt 'LED Arduino'  # v1.16 (entfallen)
            text = ""  # v1.16: der einleitende Satz wird nicht mehr angezeigt
            red_hint = ""  # v1.09
            if is_arduino:  # v1.09
                # text = text + vbCr + vbCr + M09.Get_Language_Str("OK, wenn die LEDs am richtigen Arduino schnell blinken.")  # v1.09  # v1.15 (entfallen)
                # text = text + vbCr + vbCr + M09.Get_Language_Str("OK, wenn die LEDs am richtigen Gerät schnell blinken.")  # v1.09  # v1.15: Gerät statt Arduino  # v1.16 (entfallen)
                text = M09.Get_Language_Str("OK, wenn die LEDs am richtigen Gerät schnell blinken.")  # v1.09  # v1.15  # v1.16: ohne den einleitenden Satz
                # red_hint = M09.Get_Language_Str("Tipp: Der ausgewählte Arduino blinkt schnell")  # v1.09  # v1.14 (entfallen: Hinweis ganz entfernt)
            return {"text": text, "red_hint": red_hint, "image": self._find_image(picture)}  # v1.09

        def _switch_type(self, typ):  # v1.07
            """Zentralentyp wechseln (linker Arduino): zuletzt benutzte Variante des Typs, sonst die Standardvariante. True, wenn gewechselt wurde."""
            try:
                import proggen.M28_Diverse as M28
                cur = self._read_buildopt()
                self._remember_variant(cur)
                default = {"Nano": M02.BOARD_NANO_NEW, "ESP32": M02.BOARD_ESP32, "Pico": M02.BOARD_PICO}.get(typ)
                if default is None:
                    return False
                new = WebSelectComPort._VARIANTS.get(typ) or default
                if typ == "Nano":
                    if M28.Get_Old_Board(True) == "":
                        self._write_buildopt(new)
                    else:
                        M28.Change_Board_Typ(True, new)
                else:
                    self._write_buildopt(new)                               # ESP32 und Pico: die Build-Optionen ersetzen (Autodetect gibt es dort nicht)
                try:
                    import mlpyproggen.Prog_Generator as PG
                    if PG.global_controller.is_connection_open():
                        PG.global_controller.disconnect()                   # wie beim Wechsel in den Optionen
                except Exception:                                           # noqa: BLE001
                    logger.debug("Trennen beim Typwechsel fehlgeschlagen", exc_info=True)
                logger.info("Port-Auswahl: Zentralentyp von %r auf %s gewechselt (%r)", cur, typ, self._read_buildopt())
                return True
            except Exception:                                               # noqa: BLE001
                logger.exception("Typwechsel in der Port-Auswahl fehlgeschlagen")
                return False

        # ------------------------------------------------------------ neuer Dialog (v1.11)
        _GROUPS = ("Classic", "Pro", "Pico")                                # Reihenfolge der Gruppen; danach 'unbekannt'
        _new_layout = False
        _rows = []
        _sel_dev = None
        _prev_devs = None
        _stored_port = ""

        @staticmethod
        def _norm_port(p):  # v1.11: gespeicherter Anschluss aus dem Blatt; alte Zahlen, ' ' und '999' gelten als 'keiner'
            s = "" if p is None else str(p).strip()
            return "" if s in ("", "999") or s.lstrip("-").isdigit() else s

        def _sheet_group(self):  # v1.11: Gruppe des im Blatt eingestellten Boards
            import proggen.M02a_Public as M02a
            bt = M02a.Get_BoardTyp()
            return "Pro" if bt == M02.HT_ESP32 else ("Pico" if bt == M02.HT_PICO else "Classic")

        def _row(self, dev):  # v1.11
            return next((r for r in self._rows if r["dev"] == dev), None)

        def _apply_group(self, group):  # v1.11: Board des Blattes auf die Gruppe umstellen (Abbrechen macht es ueber _orig_buildopt rueckgaengig)
            if group == self._sheet_group():
                return False
            return self._switch_type({"Classic": "Nano", "Pro": "ESP32", "Pico": "Pico"}[group])

        def _classify_group(self, comport):  # v1.11
            t = M07.Classify_Port(comport)
            if not t:
                d = str(getattr(comport, "description", "") or "")
                if "USB Serial Port" in d or "tty" in d:                    # wie die Nano-Erkennung im Excel-Programm
                    t = "Nano"
            return {"Nano": "Classic", "ESP32": "Pro", "Pico": "Pico"}.get(t, "unbekannt")

        def _scan(self):  # v1.11: alle Anschluesse [(Gruppe, Anschluss, Beschreibung)]
            import re
            res = []
            try:
                for cp in M07.portlist.comports(include_links=False):
                    if os.name != "nt" and re.match(r"^/dev/ttyS\d+$", str(cp.device)) and str(cp.hwid).strip().lower() in ("n/a", ""):
                        continue                                            # Linux: Platzhalter ohne Geraet
                    res.append((self._classify_group(cp), str(cp.device), str(cp.description or "").strip()))
            except Exception:                                               # noqa: BLE001
                logger.debug("Anschluesse konnten nicht gelesen werden", exc_info=True)
            return res

        def _compute_new(self):  # v1.11: Liste aufbauen, Auswahl bestimmen, Ident und Blinken (M07.CheckCOMPort) nachfuehren
            import re
            sheet = self._sheet_group()
            stored = self._stored_port
            found = self._scan()
            all_devs = {d for _t, d, _n in found}
            rows = []
            for typ, dev, desc in found:
                if dev == stored and typ == "unbekannt":
                    typ = sheet                                             # der im Blatt eingetragene Anschluss gilt als Board des Blattes
                if typ == "unbekannt" and not self._show_unknown:
                    continue
                rows.append({"typ": typ, "dev": dev, "desc": desc, "offline": False})
            if stored and stored not in all_devs:
                rows.append({"typ": sheet, "dev": stored, "desc": "", "offline": True})   # das Board des Blattes steht immer in der Liste

            def key(r):
                m = re.search(r"(\d+)$", r["dev"])
                g = self._GROUPS.index(r["typ"]) if r["typ"] in self._GROUPS else len(self._GROUPS)
                return (g, int(m.group(1)) if m else 0, r["dev"])
            rows.sort(key=key)
            devs = [r["dev"] for r in rows]
            online = [r for r in rows if not r["offline"]]
            sel = self._sel_dev
            if sel not in devs:
                new = [d for d in devs if self._prev_devs is not None and d not in self._prev_devs and not self._row_offline(rows, d)]
                if new:
                    sel = new[0]                                            # neu angeschlossenes Geraet wird gewaehlt
                elif stored in devs:
                    sel = stored
                else:
                    pref = [r for r in online if r["typ"] == sheet] or online or rows
                    sel = pref[0]["dev"] if pref else None
            self._prev_devs = devs
            self._rows, self._sel_dev = rows, sel
            ns["LocalComPorts"] = devs
            ns["PortNames"] = [r["desc"] or r["dev"] for r in rows]
            if not rows:
                M07.CheckCOMPort = "999"
                if self._old_comport is not None:
                    import proggen.M07_COM_Port_New as M07New
                    M07New._Ident_Send_Cmd(self._old_comport, M07New._Ident_Board(), "~MLLIDENT 0")
                    self._old_comport = None
                return
            idx = devs.index(sel)
            cur = rows[idx]
            M07.CheckCOMPort_Txt = ns["PortNames"][idx]
            M07.CheckCOMPort = "999" if cur["offline"] else cur["dev"]       # offline: nichts blinken lassen
            self.Com_Port_No = idx
            self._sel_index = idx
            new_comport = None if cur["offline"] else cur["dev"]
            old_comport = self._old_comport
            if new_comport != old_comport:
                import proggen.M07_COM_Port_New as M07New
                if old_comport is not None:
                    M07New._Ident_Send_Cmd(old_comport, M07New._Ident_Board(), "~MLLIDENT 0")
                if new_comport is not None:
                    M07New.Ident_Send_Keepalive(new_comport)
                self._old_comport = new_comport
            old_ = ns["OldL_ComPorts"]
            if not M30.isInitialised(old_) or list(old_) != devs:
                logger.info("Anschluesse: %s (Blatt: %s, unbekannte Ports anzeigen: %s, gewaehlt: %s)",
                            ["%s:%s%s" % (r["typ"], r["dev"], "(offline)" if r["offline"] else "") for r in rows], sheet, self._show_unknown, sel)
            ns["OldL_ComPorts"] = devs

        @staticmethod
        def _row_offline(rows, dev):  # v1.11
            return any(r["dev"] == dev and r["offline"] for r in rows)

        # ------------------------------------------------------------ Aktualisierung (auch aus dem Zeitgeber-Thread)
        def _compute(self, DefaultPort):
            LocalComPorts, PortNames = M07.EnumComPorts(self._show_unknown, ns["PortNames"], PrintDebug=ns["LocalPrintDebug"])
            ns["LocalComPorts"], ns["PortNames"] = LocalComPorts, PortNames
            if not M30.isInitialised(LocalComPorts):
                M07.CheckCOMPort = "999"
                # Kein Port verfuegbar: _old_comport zuruecksetzen und Ident_Stop senden  # v1.10
                if self._old_comport is not None:  # v1.10
                    import proggen.M07_COM_Port_New as M07New  # v1.10
                    M07New._Ident_Send_Cmd(self._old_comport, M07New._Ident_Board(), "~MLLIDENT 0")  # v1.10
                    self._old_comport = None  # v1.10
                return [], "", ""
            spin = self._sel_index
            spin_max = len(LocalComPorts) - 1
            # if DefaultPort != " ":  # v1.05 (entfallen)
            if DefaultPort not in (" ", 0, "", None):                       # 0 heisst 'keine Vorgabe' (so ruft der Zeitgeber der blinkenden LEDs auf): sonst wurde ein neu angeschlossenes Geraet nie gewaehlt  # v1.05
                for i in range(len(LocalComPorts)):
                    if DefaultPort == LocalComPorts[i]:
                        spin = i
            else:
                old = ns["OldL_ComPorts"]
                if M30.isInitialised(old) and len(LocalComPorts) > len(old):
                    spin = len(LocalComPorts) - 1                           # ein Anschluss ist dazugekommen und steht am Ende: der neue wird gewaehlt  # v1.05
                    for ix in range(len(old)):
                        if LocalComPorts[ix] != old[ix]:
                            spin = ix
                            break
            spin = max(0, min(spin, spin_max))
            if PortNames == []:
                PortNames.append(" ")
                LocalComPorts.append(" ")
            M07.CheckCOMPort_Txt = PortNames[spin]
            port = LocalComPorts[spin]
            M07.CheckCOMPort = "999" if port == " " else port
            self.Com_Port_No = spin
            self._sel_index = spin

            # Pruefen ob sich der COM Port geaendert hat  # v1.10
            new_comport = port if port not in (" ", "999") else None  # v1.10
            old_comport = self._old_comport  # v1.10

            if new_comport != old_comport and (new_comport is not None or old_comport is not None):  # v1.10
                # COM Port hat sich geaendert: Ident_Stop an alten, Ident_Send_Keepalive an neuen  # v1.10
                logger.debug("COM Port gewechselt: %s -> %s", old_comport, new_comport)  # v1.10
                if old_comport is not None:  # v1.10
                    import proggen.M07_COM_Port_New as M07New  # v1.10
                    M07New._Ident_Send_Cmd(old_comport, M07New._Ident_Board(), "~MLLIDENT 0")  # v1.10
                if new_comport is not None:  # v1.10
                    import proggen.M07_COM_Port_New as M07New  # v1.10
                    M07New.Ident_Send_Keepalive(new_comport)  # v1.10
                self._old_comport = new_comport  # v1.10

            old_ = ns["OldL_ComPorts"]  # v1.05
            if not M30.isInitialised(old_) or list(old_) != list(LocalComPorts):  # v1.05
                try:                                                        # nur wenn sich die Liste aendert: die Zeile im Protokoll zeigt, was das Programm sieht (Anschluesse, Board, unbekannte Ports)  # v1.05
                    import proggen.M02a_Public as _M02a  # v1.05
                    logger.info("Anschluesse: %s (Board %s, unbekannte Ports anzeigen: %s, gewaehlt: %s)", list(LocalComPorts), _M02a.Get_BoardTyp(), self._show_unknown, port)  # v1.05
                except Exception:                                           # noqa: BLE001  # v1.05
                    logger.debug("Anschlussliste nicht protokolliert", exc_info=True)  # v1.05
            ns["OldL_ComPorts"] = LocalComPorts
            avail_txt = M30.DelLast("".join(p + " " for p in LocalComPorts)) if LocalComPorts else ""
            try:                                                            # v1.06/v1.07: "Andere Typen" als anklickbare Liste (Anschluss, Typ)
                self._other = M07.Other_Type_Port_List()
            except Exception:                                               # noqa: BLE001
                self._other = []
            return LocalComPorts, port, avail_txt

        def Update_SpinButton(self, DefaultPort):
            if not getattr(self, "IsActive", False):  # v1.03
                # Kein Dialog offen (geschlossen oder nie geoeffnet): den Zeitgeber der blinkenden LEDs beenden (CheckCOMPort = " "). Ohne das setzte das Tk-Original unten
                # CheckCOMPort immer wieder auf den ersten Port, der Zeitgeber lief endlos und oeffnete den Port jede Sekunde (esptool: Zugriff verweigert).
                M07.CheckCOMPort = " "  # v1.03
                return  # v1.03
            if not wd.bridge_usable() and self._ui is None:
                return super().Update_SpinButton(DefaultPort)
            if not self.isInitialised:
                return
            if self._new_layout:  # v1.11
                self._compute_new()
                ui_ = self._ui
                if ui_ and ui_.get("render_list"):
                    ui_["loop"].call_soon_threadsafe(ui_["render_list"])
                if self._sel_index != self._old_spin:
                    self._old_spin = self._sel_index
                    self.Show_Status(False, M09.Get_Language_Str("Aktualisiere Status ..."))
                return
            ports, port, avail = self._compute(DefaultPort)
            ui_ = self._ui
            if ui_ and ui_["select"] is not None:
                def apply():
                    sel = ui_["select"]
                    sel.set_options(ports, value=port if port in ports else None)
                    ui_["avail"].set_text(avail)
                    ui_["render_other"]()  # v1.07
                ui_["loop"].call_soon_threadsafe(apply)
            if self._sel_index != self._old_spin:
                self._old_spin = self._sel_index
                self.Show_Status(False, M09.Get_Language_Str("Aktualisiere Status ..."))

        def Show_Status(self, ErrBox, Msg):
            if not self.isInitialised or self._ui is None:
                return
            ui_ = self._ui

            def apply():
                if ErrBox:
                    ui_["error"].set_text(str(Msg))
                    ui_["error"].set_visibility(True)
                    ui_["status"].set_visibility(False)
                else:
                    ui_["status"].set_text(str(Msg))
                    # ui_["status"].set_visibility(True)  # v1.17 (entfallen)
                    ui_["status"].set_visibility(not getattr(self, "_new_layout", False))  # v1.17: Geraeteauswahl: Name des Anschlusses steht schon in der Liste, keine Statuszeile darueber
                    ui_["error"].set_visibility(False)
            ui_["loop"].call_soon_threadsafe(apply)

        # ------------------------------------------------------------ Dialog
        def ShowDialog(self, Caption, Title, Text, Picture, Buttons, FocusButton, Show_ComPort, Red_Hint,
                       ComPort_IO, PrintDebug=False):
            if not wd.bridge_usable():
                return super().ShowDialog(Caption, Title, Text, Picture, Buttons, FocusButton, Show_ComPort,
                                          Red_Hint, ComPort_IO, PrintDebug)
            wlan_device = InStr(P01.Cells(M02.SH_VARS_ROW, M25.BUILDOP_COL), "WLAN") > 0
            if wlan_device:
                Caption = M09.Get_Language_Str("Überprüfung des mDNS-Gerät")
                Title = M09.Get_Language_Str("Auswahl der mDNS-IP Adresse")
                Text = M09.Get_Language_Str("Es werden alle mDNS-IP Adressen gesucht mit denen sich ein MLL-Gerät meldet.")
                Red_Hint = ""
                Picture = "PICOWL_Image"
            buttons = split_buttons(Buttons)
            if len(Buttons.split(";")) != 3:
                P01.MsgBox("Internal Error in Select_COM_Port_UserForm: 'Buttons' must be a string with 3 buttons "
                           "separated by ';'" + vbCr + "Wrong: '" + Buttons + "'", vbCritical, "Internal Error")
                M30.EndProg()
            windows = P01.checkplatform("Windows") is True
            # self._show_unknown = not windows  # v1.04 (entfallen)
            self._show_unknown = self._initial_show_unknown(windows)  # v1.04
            hints = info["hints"]
            hint = ""
            if Show_ComPort and hints:
                hint = hints[0] if not windows else (hints[1] if len(hints) > 1 else hints[0])
                if wlan_device and len(hints) > 2:
                    hint = hints[2]
                hint = M09.Get_Language_Str(hint)
            image = ""
            # img_file = os.path.join(here, "images", Picture + ".png")  # v1.08 (entfallen)
            # if os.path.exists(img_file):  # v1.08 (entfallen)
            #     image = "/mll_images/" + Picture + ".png"  # v1.08 (entfallen)
            try:  # v1.08: Dateiname ohne Beachtung der Gross-/Kleinschreibung (LED_Image -> LED_image.png), sonst fehlt das Bild unter Linux
                wanted = (Picture + ".png").lower()  # v1.08
                found = next((f for f in os.listdir(os.path.join(here, "images")) if f.lower() == wanted), None)  # v1.08
            except OSError:  # v1.08
                found = None  # v1.08
            if found:  # v1.08
                image = "/mll_images/" + found  # v1.08
            self.title = M09.Get_Language_Str(Caption)
            self._old_spin = -1
            self._sel_index = -1
            self._old_comport = None  # Zuruecksetzen beim Oeffnen des Dialogs  # v1.10
            ns["__LocalPrintDebug"] = PrintDebug
            ns["Pressed_Button"] = 0
            ports, port, avail = [], "", ""
            self.isInitialised = False
            self._other = []  # v1.07
            self._orig_buildopt = None  # v1.07: Build-Optionen beim Oeffnen, fuer 'Abbrechen' nach einem Typwechsel
            if Show_ComPort and not wlan_device:  # v1.07
                self._orig_buildopt = self._read_buildopt()
                self._remember_variant(self._orig_buildopt)
            self._new_layout = bool(Show_ComPort and not wlan_device and Picture in ("LED_Image", "ESP32_Image", "PICO_Image"))  # v1.11
            if self._new_layout:  # v1.11: neuer Dialog der Lichtmaschine
                self._show_unknown = False
                self._rows, self._sel_dev, self._prev_devs = [], None, None
                self._stored_port = self._norm_port(ComPort_IO)
                self._compute_new()
                view = self._board_view()
                tr = M09.Get_Language_Str
                hint = tr("Zur Identifikation blinken die LEDs des ausgewählten Geräts schnell.\nEin anderes Gerät kann in der obigen Liste gewählt werden.\n"  # v1.14: Hinweis zur Liste (statt Pfeiltasten)
                          "Das Gerät kann auch nachträglich angesteckt werden.")  # v1.14
                spec = {"title": Title, "text": view["text"], "red_hint": view["red_hint"], "image": view["image"] or image, "hint": hint, "buttons": buttons,
                        "list_title": tr("Gefundene Geräte"), "unknown_text": tr(info["unknown"] or "Unbekante Ports anzeigen"),  # v1.14: Geräte statt Boards
                        # "none_text": tr("Kein Board gefunden. Bitte das Board per USB anschließen."),  # v1.15 (entfallen)
                        "none_text": tr("Kein Gerät gefunden. Bitte das Gerät per USB anschließen."),  # v1.15: Gerät statt Board
                        "col_type": tr("Typ"), "col_port": tr("Port"), "offline_text": tr("offline"),
                        "groups": {"Classic": "Classic (Nano / Uno)", "Pro": "Pro (ESP32)", "Pico": "Pico (Raspberry Pico)", "unbekannt": tr("Unbekannt")},
                        "types": {"unbekannt": tr("unbekannt")},
                        "ask_text": tr("Um welchen Typ handelt es sich bei %1?"), "no_text": tr("Abbrechen"),
                        "ask_options": {"Classic": "Classic (Nano / Uno)", "Pro": "Pro (ESP32)", "Pico": "Pico (Raspberry Pico)"}}
                self.IsActive = True
                pressed = wd.call_in_loop(_comport_async_new, self, spec, default=2)
                self.IsActive = False
                if self._old_comport is not None:
                    import proggen.M07_COM_Port_New as M07New
                    M07New._Ident_Send_Cmd(self._old_comport, M07New._Ident_Board(), "~MLLIDENT 0")
                    self._old_comport = None
                M07.CheckCOMPort = " "
                if pressed != 3:                                            # Abbrechen: Typwechsel rueckgaengig machen
                    if self._orig_buildopt is not None and self._read_buildopt() != self._orig_buildopt:
                        self._write_buildopt(self._orig_buildopt)
                        logger.info("Typwechsel in der Port-Auswahl durch Abbrechen rueckgaengig gemacht")
                ns["Pressed_Button"] = pressed
                if self._sel_dev:
                    ComPort_IO = self._sel_dev
                self._new_layout = False
                return pressed, ComPort_IO
            if Show_ComPort:
                ports, port, avail = self._compute(ComPort_IO)
                # _old_comport initialisieren nach dem ersten _compute  # v1.10
                self._old_comport = port if port not in (" ", "999") else None  # v1.10
            spec = {"title": Title, "text": Text, "red_hint": Red_Hint, "image": image, "show_port": Show_ComPort,
                    "ports": ports, "port": port if port in ports else None, "avail": avail,
                    "unknown_text": M09.Get_Language_Str(info["unknown"] or "Unbekante Ports anzeigen"),
                    "show_unknown": self._show_unknown, "hint": hint, "buttons": buttons,
                    "other_text": M09.Get_Language_Str("Andere Typen:"),
                    "switch_text": M09.Get_Language_Str("Zentrale auf %1 umstellen und %2 verwenden?"),
                    "yes_text": M09.Get_Language_Str("Ja"), "no_text": M09.Get_Language_Str("Nein"),  # v1.07
                    "main_col": Picture in ("LED_Image", "ESP32_Image", "PICO_Image", "PICOWL_Image")}  # v1.09: nur der Dialog der Lichtmaschine wechselt Bild und Text
            self.IsActive = True
            pressed = wd.call_in_loop(_comport_async, self, spec, default=2)
            self.IsActive = False
            # Ident_Stop an den aktiven COM Port senden beim Schliessen des Dialogs  # v1.10
            if self._old_comport is not None:  # v1.10
                import proggen.M07_COM_Port_New as M07New  # v1.10
                M07New._Ident_Send_Cmd(self._old_comport, M07New._Ident_Board(), "~MLLIDENT 0")  # v1.10
                self._old_comport = None  # v1.10
            M07.CheckCOMPort = " "
            if pressed == 2 and self._orig_buildopt is not None and self._read_buildopt() != self._orig_buildopt:  # v1.07: Abbrechen macht den Typwechsel rueckgaengig
                self._write_buildopt(self._orig_buildopt)
                logger.info("Typwechsel in der Port-Auswahl durch Abbrechen rueckgaengig gemacht")
            ns["Pressed_Button"] = pressed
            if Show_ComPort and M30.isInitialised(ns["LocalComPorts"]):
                ComPort_IO = ns["LocalComPorts"][max(0, min(self.Com_Port_No, len(ns["LocalComPorts"]) - 1))]
            return pressed, ComPort_IO

    return WebSelectComPort


def install_instance(F00):
    orig = getattr(F00, "Select_COM_Port_UserForm", None)
    if orig is not None and not getattr(type(orig), "_is_web", False):
        cls = make_class(type(orig))
        cls._is_web = True
        F00.Select_COM_Port_UserForm = cls()
        logger.info("Web-Formular installiert (Select_COM_Port_UserForm)")
