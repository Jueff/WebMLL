# Datei-Version: 1.00 (2026-11-25) - headless_sheet_settings.py
# ----------------------------------------------------------------------------------------------
# Name:           headless_sheet_settings.py
# Path:           headless/headless_sheet_settings.py
# Version:        1.00
# Last Update:    2026-11-25
# Author:         Jürgen Winkler
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-25  Neu: Einstellungen der Hauptplatine (Optionen, Reiter Lichtmaschine -> Einstellungen) im Blatt. 'Lichtsensor aktivieren' und 'Schaltzustaende
#                     speichern' sind Makrozeilen des Blattes (#define READ_LDR, #define ENABLE_STORE_STATUS()): sie werden hier gesetzt (Zeile einfuegen oder eine
#                     ausgeschaltete/versteckte Zeile einschalten) und entfernt (Zeilen loeschen). Die frueheren Schluessel 'ldr' und 'store_status' in esp32_options
#                     werden dabei in Makrozeilen uebernommen (migrate_legacy).
# ----------------------------------------------------------------------------------------------
"""Einstellungen des Blattes, die als Makrozeile im Blatt stehen.

Der Code-Generator (M06_Write_Header_SW) erkennt die Zeilen '#define READ_LDR' und '#define ENABLE_STORE_STATUS' in der Makrospalte. Damit ist die Makrozeile die
einzige Stelle, an der die Einstellung steht: sie wird mit dem Blatt gespeichert, exportiert und kopiert, und der Anwender sieht sie in der Tabelle."""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Schluessel -> (Makrotext wie in Lib_Macros, Beschreibung der Zeile)
MACROS = {
    "ldr": ("#define READ_LDR", "Lichtsensor aktivieren"),
    "store_status": ("#define ENABLE_STORE_STATUS()", "Schaltzustände speichern"),
}


def norm_macro(text) -> str:
    """'#define  ENABLE_STORE_STATUS() ' -> '#define ENABLE_STORE_STATUS' (Leerzeichen zusammengefasst, '()' am Ende entfaellt)"""
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if t.endswith("()"):
        t = t[:-2].rstrip()
    return t


def _modules():
    import ExcelAPI.XLA_Application as P01
    import proggen.M02_Public as M02
    import proggen.M25_Columns as M25
    import proggen.M30_Tools as M30
    return P01, M02, M25, M30


def macro_rows(key: str, sheet=None) -> list:
    """Zeilen (1-basiert) des Blattes mit dem Makro der Einstellung: [(Zeile, aktiv)]. Aktiv = nicht versteckt und eingeschaltet (Haken in Spalte B)."""
    P01, M02, M25, M30 = _modules()
    ws = sheet or P01.ActiveSheet
    if ws is None:
        return []
    M25.Make_sure_that_Col_Variables_match(ws)
    target = norm_macro(MACROS[key][0])
    res = []
    last = int(M30.LastUsedRowIn(ws) or 0)
    for r in range(M02.FirstDat_Row, last + 2):
        if norm_macro(ws.Cells(r, M25.Config__Col).Value) != target:
            continue
        hidden = bool(ws.Rows(r).EntireRow.Hidden)
        enabled = str(ws.Cells(r, M02.Enable_Col).Value or "") != ""
        res.append((r, enabled and not hidden))
    return res


def is_set(key: str, sheet=None) -> bool:
    """Steht die Einstellung im Blatt? (aktive Makrozeile oder der fruehere Schluessel in esp32_options)"""
    P01 = _modules()[0]
    ws = sheet or P01.ActiveSheet
    if any(active for _r, active in macro_rows(key, ws)):
        return True
    return (getattr(ws, "esp32_options", None) or {}).get(key) is True


def set_macro(key: str, value: bool, sheet=None, description: str | None = None) -> bool:
    """Makrozeile der Einstellung setzen (value True) oder entfernen (False). True, wenn sich das Blatt geaendert hat.
    Setzen: eine vorhandene, ausgeschaltete oder versteckte Zeile wird eingeschaltet, sonst wird oben im Blatt eine Zeile eingefuegt.
    Entfernen: alle Zeilen mit dem Makro werden geloescht (auch ausgeschaltete, damit die Einstellung nicht spaeter unbemerkt wieder wirkt)."""
    P01, M02, M25, _M30 = _modules()
    ws = sheet or P01.ActiveSheet
    if ws is None:
        return False
    rows = macro_rows(key, ws)
    macro, desc = MACROS[key]
    changed = False
    old_events = P01.Application.EnableEvents
    if value:
        if any(active for _r, active in rows):
            return False
        ws.Activate()
        P01.Application.EnableEvents = False
        try:
            if rows:                                                        # vorhandene Zeile einschalten und zeigen
                r = rows[0][0]
                P01.CellDict[r, M02.Enable_Col] = chr(M02.Hook_CHAR)
                try:
                    P01.Rows(r).EntireRow.Hidden = False
                except Exception:                                           # noqa: BLE001
                    logger.debug("Zeile %s nicht eingeblendet", r, exc_info=True)
                logger.info("Einstellungen des Blattes %s: Zeile %s mit %s eingeschaltet", ws.Name, r, macro)
            else:                                                           # neue Zeile oben im Blatt (wie die Konfigurationszeilen der Beispiele)
                r = M02.FirstDat_Row
                ws.tksheet.insert_rows(rows=1, idx=r - 1)
                P01.CellDict[r, M02.Enable_Col] = chr(M02.Hook_CHAR)
                P01.CellDict[r, M25.Descrip_Col] = description or desc
                P01.CellDict[r, M25.Config__Col] = macro
                logger.info("Einstellungen des Blattes %s: Zeile %s mit %s eingefuegt", ws.Name, r, macro)
            changed = True
        finally:
            P01.Application.EnableEvents = old_events
    else:
        if not rows:
            return False
        from headless import headless_graph_ops as GO
        for r, _active in sorted(rows, reverse=True):                       # von unten nach oben: die Zeilennummern darueber bleiben gueltig
            GO.delete_row(ws, r - 1)
            logger.info("Einstellungen des Blattes %s: Zeile %s mit %s geloescht", ws.Name, r, macro)
        changed = True
    if changed:
        try:
            import proggen.M20_PageEvents_a_Functions as M20
            M20.Update_Start_LedNr()
        except Exception:                                                   # noqa: BLE001
            logger.debug("LED-Nummern nicht neu gerechnet", exc_info=True)
    return changed


def migrate_legacy(sheet=None) -> bool:
    """Fruehere Schluessel 'ldr' und 'store_status' in esp32_options in Makrozeilen uebernehmen und aus esp32_options entfernen. True, wenn sich etwas geaendert hat."""
    P01 = _modules()[0]
    ws = sheet or P01.ActiveSheet
    opts = dict(getattr(ws, "esp32_options", None) or {})
    changed = False
    for key in MACROS:
        if key in opts:
            if opts.pop(key) is True:
                set_macro(key, True, ws)
            changed = True
    if changed:
        ws.esp32_options = opts
    return changed


def apply(key: str, value: bool, sheet=None, description: str | None = None) -> bool:
    """Einstellung aus dem Optionen-Dialog uebernehmen: Makrozeile setzen/entfernen und den frueheren Schluessel in esp32_options loeschen."""
    P01 = _modules()[0]
    ws = sheet or P01.ActiveSheet
    opts = dict(getattr(ws, "esp32_options", None) or {})
    if key in opts:
        opts.pop(key)
        ws.esp32_options = opts
    return set_macro(key, bool(value), ws, description)
