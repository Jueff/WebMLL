# Datei-Version: 1.01 (2026-11-19) - M42_Dyn_Config.py
# ----------------------------------------------------------------------------------------------
# Name:           M42_Dyn_Config.py
# Path:           proggen/M42_Dyn_Config.py
# Version:        1.01
# Last Update:    2026-11-19
# Author:         Harold Linke
# Licence:        LGPL V2.1
# History of Change:
#   1.01  2026-11-19  Ausgabefenster: Der schnelle Weg zeigt, dass nur die Konfiguration uebertragen wird, den Fortschritt (25-%-Schritte) und die Fertigstellung; bei einem Rueckfall auf das ganze Programm steht der Grund da (Zeilen mit '# v1.01')
#   1.00  2026-11-19  Neu: ESP32 und Pico: Das Programm wird nur noch hochgeladen, wenn sich Quellcode, Erweiterungen oder Einstellungen aendern; sonst geht nur die Konfiguration
#                     ueber die serielle Schnittstelle zum Geraet (Einstellung 'serial_cfg'). Die Arbeit steckt in headless/headless_dyn_config.py
#                     ATmega (Nano/Uno) bleibt unveraendert: Decide() und Upload_Possible() gelten nur fuer ESP32 und Pico. Die Signatur der Firmware steht auch in der Konfigurationsdatei.
# ----------------------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Anbindung der Funktion 'Konfiguration getrennt von der Firmware' an den Programm Generator

Ablauf:
  1. M06 fragt Decide(): Ist die Funktion eingeschaltet und moeglich? Dann schreibt es die Kopfdatei im Modus MLL_DYNAMIC_CONFIG.
  2. M06 ruft Finalize(): Konfigurationsdatei erzeugen, Signatur berechnen und in die Kopfdatei eintragen. Scheitert das, wird die Kopfdatei klassisch neu geschrieben.
  3. M08 ruft vor dem Uebersetzen Try_Config_Only(): Meldet das Geraet dieselbe Signatur, geht nur die Konfiguration hin und es wird nichts uebersetzt oder geflasht.
  4. Nach einem vollstaendigen Hochladen ruft M08 After_Full_Flash(): Die Konfiguration wird hinterher geschickt.
"""
import logging
import os
import time  # v1.01

import headless.headless_dyn_config as DC
import proggen.M02_Public as M02
import proggen.M02a_Public as M02a
import proggen.M25_Columns as M25
import proggen.M28_Diverse as M28
import proggen.M30_Tools as M30
import proggen.M09_Language as M09
import mlpyproggen.Prog_Generator as PG
import ExcelAPI.XLA_Application as P01

log = logging.getLogger("webmobaledlib.arduino")

OPTION_KEY = "serial_cfg"

_state = {"active": False, "off": False, "tools": None, "tools_checked": False, "env": "", "pico": False, "sig": "", "blob": None, "blob_file": "", "output": False}  # v1.01


def Option_Enabled():
    try:
        return bool(PG.global_controller.getConfigData(OPTION_KEY))
    except Exception:                                      # noqa: BLE001
        return False


def Set_Option(value):
    PG.global_controller.setConfigData(OPTION_KEY, bool(value))
    PG.global_controller.SaveConfigData()


def Active():
    """True wenn die zuletzt erzeugte Kopfdatei im Modus MLL_DYNAMIC_CONFIG geschrieben wurde"""
    return _state["active"]


def Environment():
    return _state["env"]


def Disable_Once(reason):
    """Die naechste Kopfdatei wird klassisch geschrieben (nach einem Fehler in Finalize)"""
    log.warning("Konfiguration getrennt von der Firmware: %s - es wird das ganze Programm hochgeladen", reason)
    _state["off"] = True
    _state["active"] = False


def _is_ip(text):
    return isinstance(text, str) and "IP:" in text


def _tools():
    if not _state["tools_checked"]:
        _state["tools_checked"] = True
        extra_bin, extra_plat = [], []
        try:
            import proggen.M08_ARDUINO as M08
            ide = M30.FilePath(M08.Find_ArduinoExe())
            if ide:
                extra_bin.append(os.path.join(ide, "hardware", "tools", "avr", "bin"))
                extra_plat.append(os.path.join(ide, "hardware", "arduino", "avr"))
        except BaseException:                              # noqa: BLE001
            pass
        tools = DC.find_avr_tools(extra_bin, extra_plat)
        if tools is None:
            try:
                import proggen.M08_ARDUINO as M08
                P01.set_statusmessage(M09.Get_Language_Str("AVR-Werkzeuge werden mit PlatformIO installiert (einmalig) ..."))
                if DC.install_avr_tools(M08.Find_PIO()):
                    tools = DC.find_avr_tools(extra_bin, extra_plat)
            except BaseException as e:                     # noqa: BLE001
                log.warning("Konfiguration getrennt: AVR-Werkzeuge konnten nicht installiert werden: %s", e)
        _state["tools"] = tools
        if tools:
            log.info("Konfiguration getrennt: AVR-Werkzeuge in %s", tools["bin"])
    return _state["tools"]


def Decide(CreateFilesOnly, HeaderOnly):
    """Soll die Kopfdatei im Modus MLL_DYNAMIC_CONFIG geschrieben werden?"""
    _state["active"] = False
    _state["output"] = False  # v1.01
    off = _state["off"]
    _state["off"] = False                                  # gilt nur fuer einen Durchlauf
    if not Option_Enabled() or CreateFilesOnly or HeaderOnly or off:
        return False
    board = M02a.Get_BoardTyp()
    if board not in (M02.HT_ESP32, M02.HT_PICO):
        return False
    why = ""
    port = P01.Cells(M02.SH_VARS_ROW, M25.COMPort_COL)
    if not M28.Is_PlatformIO():
        why = "nur mit PlatformIO moeglich"
    elif _is_ip(port) or (board == M02.HT_ESP32 and P01.Cells(M02.SH_VARS_ROW, M25.COMPort_COL + 1) not in ("", None)):
        why = "nicht beim Hochladen per WLAN (IP-Adresse)"
    elif _tools() is None:
        why = "die AVR-Werkzeuge (avr-g++ und Arduino-Kern) fehlen"
    if why:
        log.warning("Konfiguration getrennt von der Firmware ist eingeschaltet, aber %s - es wird das ganze Programm hochgeladen", why)
        return False
    _state.update(active=True, env="pico" if board == M02.HT_PICO else "esp32", pico=(board == M02.HT_PICO), sig="", blob=None, output=False)  # v1.01
    return True


def _lib_src(project_dir):
    lib = project_dir + "/libraries/MobaLedLib/src"
    if not os.path.isfile(lib + "/MobaLedLib.h"):
        lib = M30.DelLast(M02a.Get_Ardu_LibDir()) + "/MobaLedLib/src"
    return lib


def Finalize(header_path):
    """Nach dem Schreiben der Kopfdatei: Konfigurationsdatei erzeugen, Signatur eintragen. False bei einem Fehler."""
    try:
        import proggen.M08_ARDUINO as M08
        sketch_dir = os.path.dirname(os.path.abspath(header_path))
        project_dir = os.path.dirname(sketch_dir)
        env = _state["env"]
        if not M08.Write_PIO_Project(env, sketch_dir + os.sep):         # platformio.ini gehoert zur Signatur
            raise DC.DynConfigError("platformio.ini konnte nicht geschrieben werden")
        with open(header_path, "rb") as fh:
            raw = fh.read()
        sig = DC.compute_signature(raw.decode("utf-8", errors="replace"), sketch_dir, header_path, project_dir, os.path.join(project_dir, "platformio.ini"), env)
        workdir = os.path.join(project_dir, M02.Cfg_Dir_LED.strip("/\\"), "dyn")
        blob = DC.build_blob(sketch_dir, _lib_src(project_dir), _state["tools"], workdir, sig)
        blob_file = os.path.join(workdir, "mllcfg.bin")
        with open(blob_file, "wb") as fh:
            fh.write(blob)
        placeholder = DC.SIG_PLACEHOLDER.encode("ascii")
        if placeholder not in raw:
            raise DC.DynConfigError("Die Signatur fehlt in der Kopfdatei")
        with open(header_path, "wb") as fh:
            fh.write(raw.replace(placeholder, sig.encode("ascii")))
    except BaseException as e:                             # noqa: BLE001
        log.warning("Konfiguration getrennt von der Firmware: %s", e)
        _state["active"] = False
        return False
    _state.update(sig=sig, blob=blob, blob_file=blob_file)
    log.info("Konfiguration getrennt von der Firmware: Signatur %s, Konfigurationsdatei %d Bytes (%s)", sig, len(blob), blob_file)
    return True


def Upload_Possible(Mode, ComPort):
    """Gilt fuer den Upload, der gerade ansteht (M08)? """
    return (_state["active"] and _state["blob"] is not None and Mode in (M02.HT_ESP32, M02.HT_PICO) and not _is_ip(ComPort)
            and M28.Is_PlatformIO() and getattr(PG.global_controller, "execute_upload", True))


def _status(text):
    try:
        P01.set_statusmessage(text)
    except Exception:                                      # noqa: BLE001
        pass
    log.info(text)


def _t(text, **values):  # v1.01
    """Text in der eingestellten Sprache (Katalog csv/Web_Languages.csv); ohne die Web-Uebersetzung bleibt er deutsch"""  # v1.01
    try:  # v1.01
        from _web.web_i18n import tr  # v1.01
        return tr(text, **values)  # v1.01
    except Exception:                                      # noqa: BLE001  # v1.01
        return text.format(**values) if values else text  # v1.01


def _page():  # v1.01
    try:  # v1.01
        return PG.global_controller.getFramebyName("ARDUINOMonitorPage")  # v1.01
    except Exception:                                      # noqa: BLE001  # v1.01
        return None  # v1.01


def _out(text, highlight=None):  # v1.01
    """Zeile im Ausgabefenster (und damit im Protokoll)"""  # v1.01
    page = _page()  # v1.01
    if page is None:  # v1.01
        log.info(text)  # v1.01
        return  # v1.01
    try:  # v1.01
        if highlight:  # v1.01
            page.add_text_to_textwindow(text + "\n", highlight=highlight)  # v1.01
        else:  # v1.01
            page.add_text_to_textwindow(text + "\n")  # v1.01
    except Exception:                                      # noqa: BLE001  # v1.01
        log.info(text)  # v1.01


def _open_output():  # v1.01
    """Ausgabefenster fuer den schnellen Weg oeffnen und leeren"""  # v1.01
    _state["output"] = True  # v1.01
    page = _page()  # v1.01
    try:  # v1.01
        page.set_title(_t("Schnelles Update: Konfiguration übertragen"))  # v1.01
        page.delete_text_from_textwindow()  # v1.01
        PG.global_controller.showFramebyName("ARDUINOMonitorPage")  # v1.01
    except Exception:                                      # noqa: BLE001  # v1.01
        log.debug("Ausgabefenster nicht zu oeffnen", exc_info=True)  # v1.01


def _restore_title():  # v1.01
    """Nach dem Rueckfall auf das ganze Programm: wieder die Ueberschrift des normalen Hochladens"""  # v1.01
    try:  # v1.01
        from _web import web_log  # v1.01
        _page().set_title(web_log.DEFAULT_TITLE)  # v1.01
    except Exception:                                      # noqa: BLE001  # v1.01
        pass  # v1.01


def Output_Written():  # v1.01
    """True wenn Try_Config_Only etwas ins Ausgabefenster geschrieben hat (M08 loescht es dann beim ganzen Programm nicht, die Begruendung bleibt lesbar)"""  # v1.01
    return _state["output"]  # v1.01


def _progress():  # v1.01
    """Fortschrittsanzeige in 25-%-Schritten (die Datei hat nur wenige KB)"""  # v1.01
    nxt = [25]  # v1.01

    def callback(pos, total):  # v1.01
        pct = pos * 100 // total  # v1.01
        if pct >= nxt[0]:  # v1.01
            _out(_t("Konfiguration: {percent} % übertragen ({done} von {total} Bytes)", percent=pct, done=pos, total=total))  # v1.01
            nxt[0] = (pct // 25 + 1) * 25  # v1.01
    return callback  # v1.01


def _fallback(text, **values):  # v1.01
    """Der schnelle Weg geht nicht: Grund anzeigen, dann laedt M08 das ganze Programm hoch"""  # v1.01
    _out(_t(text, **values))  # v1.01
    _restore_title()  # v1.01
    return False  # v1.01


def Try_Config_Only(ComPort):
    """True wenn das Geraet die Firmware dieser Kopfdatei hat und die Konfiguration uebertragen wurde (oder schon aktuell ist). Sonst False: dann das ganze Programm hochladen."""
    blob = _state["blob"]
    t0 = time.time()  # v1.01
    _open_output()  # v1.01
    try:
        link = DC.Link(ComPort, dtr=_state["pico"])
    except Exception as e:                                 # noqa: BLE001
        log.info("Konfiguration getrennt: Anschluss %s nicht zu oeffnen (%s) - ganzes Programm", ComPort, e)
        return _fallback("Der Anschluss {port} lässt sich nicht öffnen ({reason}). Es wird das ganze Programm hochgeladen.", port=ComPort, reason=e)  # v1.01
    try:
        _status("Die Firmware des Geraets wird geprueft ...")
        _out(_t("Die Firmware im Gerät ({port}) wird geprüft ...", port=ComPort))  # v1.01
        info = DC.query_info(link, 8.0)
        if info is None:
            log.info("Konfiguration getrennt: das Geraet antwortet nicht (Firmware ohne diese Funktion?) - ganzes Programm")
            return _fallback("Das Gerät antwortet nicht (noch nicht programmiert oder eine Firmware ohne diese Funktion). Es wird das ganze Programm hochgeladen.")  # v1.01
        if info.get("sig") != _state["sig"]:
            log.info("Konfiguration getrennt: Firmware %s passt nicht zu %s - ganzes Programm", info.get("sig"), _state["sig"])
            return _fallback("Die Firmware im Gerät passt nicht zu dieser Konfiguration. Es wird das ganze Programm hochgeladen.")  # v1.01
        if info.get("valid") == "1" and info.get("cfg") == "%08x" % DC.blob_crc(blob):
            log.info("Konfiguration getrennt: die Konfiguration im Geraet ist schon aktuell")
            _out(_t("Die Konfiguration im Gerät ist schon aktuell. Es muss nichts übertragen werden."), "OK")  # v1.01
            return True
        _status("Die Konfiguration wird uebertragen ...")
        _out(_t("Die Firmware im Gerät passt. Das Programm wird nicht neu hochgeladen, es wird nur die Konfiguration übertragen ({n} Bytes).", n=len(blob)))  # v1.01
        DC.send_blob(link, blob, _progress())  # v1.01
        log.info("Konfiguration getrennt: %d Bytes uebertragen, das Geraet startet neu", len(blob))
        _out(_t("Fertig: Die Konfiguration wurde in {seconds} s übertragen, das Gerät startet neu.", seconds="%.1f" % (time.time() - t0)), "OK")  # v1.01
        return True
    except DC.DynConfigError as e:
        log.warning("Konfiguration getrennt: %s - ganzes Programm", e)
        return _fallback("Die Konfiguration konnte nicht übertragen werden ({reason}). Es wird das ganze Programm hochgeladen.", reason=e)  # v1.01
    finally:
        link.close()


def After_Full_Flash(ComPort):
    """Nach dem Flashen die Konfiguration schicken. True wenn sie im Geraet angekommen ist."""
    blob = _state["blob"]
    t0 = time.time()  # v1.01
    _out("")  # v1.01
    _out(_t("Das Programm ist hochgeladen. Jetzt wird die Konfiguration übertragen ..."))  # v1.01
    port = DC.wait_for_port(ComPort, _state["pico"], 25.0)
    if port is None:
        log.warning("Konfiguration getrennt: der Anschluss %s erscheint nach dem Hochladen nicht wieder", ComPort)
        _out(_t("Der Anschluss {port} erscheint nach dem Hochladen nicht wieder. Die Konfiguration wurde nicht übertragen.", port=ComPort), "Error")  # v1.01
        return False
    try:
        link = DC.Link(port, dtr=_state["pico"])
    except Exception as e:                                 # noqa: BLE001
        log.warning("Konfiguration getrennt: Anschluss %s nicht zu oeffnen: %s", port, e)
        _out(_t("Der Anschluss {port} lässt sich nicht öffnen ({reason}). Die Konfiguration wurde nicht übertragen.", port=port, reason=e), "Error")  # v1.01
        return False
    try:
        _status("Die Konfiguration wird uebertragen ...")
        info = DC.query_info(link, 20.0)
        if info is None:
            log.warning("Konfiguration getrennt: das Geraet antwortet nach dem Hochladen nicht")
            _out(_t("Das Gerät antwortet nach dem Hochladen nicht. Die Konfiguration wurde nicht übertragen."), "Error")  # v1.01
            return False
        if info.get("sig") != _state["sig"]:
            log.warning("Konfiguration getrennt: Firmware %s statt %s", info.get("sig"), _state["sig"])
        _out(_t("Die Konfiguration wird übertragen ({n} Bytes) ...", n=len(blob)))  # v1.01
        DC.send_blob(link, blob, _progress())  # v1.01
        log.info("Konfiguration getrennt: %d Bytes uebertragen, das Geraet startet neu", len(blob))
        _out(_t("Fertig: Die Konfiguration wurde in {seconds} s übertragen, das Gerät startet neu.", seconds="%.1f" % (time.time() - t0)), "OK")  # v1.01
        return True
    except DC.DynConfigError as e:
        log.warning("Konfiguration getrennt: %s", e)
        _out(_t("Die Konfiguration konnte nicht übertragen werden ({reason}).", reason=e), "Error")  # v1.01
        return False
    finally:
        link.close()
