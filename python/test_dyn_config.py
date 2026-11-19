# Datei-Version: 1.01 (2026-11-19) - test_dyn_config.py
# ----------------------------------------------------------------------------------------------
# Name:           test_dyn_config.py
# Path:           test_dyn_config.py
# Version:        1.01
# Last Update:    2026-11-19
# Author:         Harold Linke
# Licence:        LGPL V2.1
# History of Change:
#   1.01  2026-11-19  Neu: Ausgabefenster des schnellen Wegs (M42: Pruefung, Fortschritt, Fertigstellung, Rueckfall, nach dem Flashen) mit Ersatzgeraet; neue Texte in allen Sprachen
#   1.00  2026-11-19  Neu: Test der Konfiguration getrennt von der Firmware (headless_dyn_config): Dateiformat, Signatur, Pfade mit Umlauten und Leerzeichen, Protokoll mit einem Ersatzgeraet, Uebersetzung
# ----------------------------------------------------------------------------------------------
"""Aufruf: python test_dyn_config.py   (nicht geprueft werden: echtes Geraet, PlatformIO-Lauf, Oberflaeche)

Benutzt die echten Funktionen von headless/headless_dyn_config.py. Ersetzt werden nur die serielle Schnittstelle (Ersatzgeraet) und, wenn sie fehlen, die AVR-Werkzeuge (dann wird der Bau der Datei uebersprungen)."""
import os
import struct
import sys
import tempfile
import zlib
from unittest import mock

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
try:  # das echte pyserial, damit proggen.M42 importierbar ist; sonst ein Ersatz
    import serial  # noqa: E402
except ImportError:
    sys.modules["serial"] = mock.MagicMock()
    import serial  # noqa: E402

import headless.headless_dyn_config as DC  # noqa: E402

SIG = "0123456789abcdef"
Results = []


def check(name, cond, info=""):
    Results.append((name, bool(cond)))
    print(("ok     " if cond else "FEHLER ") + name + (" - " + str(info) if info and not cond else ""))


# ---------------------------------------------------------------- Dateiformat
def test_format():
    blob = DC.pack_blob(b"\x01\x02\x03", b"\x04", b"", b"\x05\x06", b"\x2c\x01\x01", 9, SIG)
    magic, ver, _, ram, l0, l1, l2, l3, l4, crc, sig = DC.BLOB_HEADER.unpack(blob[:DC.BLOB_HEADER.size])
    check("Kopf 48 Bytes", DC.BLOB_HEADER.size == 48)
    check("Kennung, Version, RAM", magic == b"MLLC" and ver == 2 and ram == 9)
    check("Laengen", (l0, l1, l2, l3, l4) == (3, 1, 0, 2, 3))
    check("CRC ueber die Nutzdaten", crc == zlib.crc32(blob[48:]) & 0xFFFFFFFF)
    check("Signatur im Kopf", sig.decode() == SIG)
    try:
        DC.pack_blob(b"", b"", b"", b"", b"", 0, "zu kurz")
        DC.build_blob(".", ".", {"bin": ".", "plat": "."}, tempfile.gettempdir(), "zu kurz")
        check("falsche Signaturlaenge wird abgelehnt", False)
    except DC.DynConfigError:
        check("falsche Signaturlaenge wird abgelehnt", True)


# ---------------------------------------------------------------- Signatur
HEADER = """// File creation: 1.1.2026
#define START_MSG "x"
#define MLL_FIRMWARE_SIG "@@MLLSIG@@"
#define INCH_A 5
#define NUM_LEDS 20
//MLLDYN_BEGIN
#ifdef CONFIG_ONLY
const uint8_t Config[] = {1, 2, 3};
#endif
//MLLDYN_END
int x = INCH_A; // Kommentar
"""


def test_signature():
    n1 = DC.normalize_header(HEADER)
    n2 = DC.normalize_header(HEADER.replace("{1, 2, 3}", "{9, 9, 9}").replace("1.1.2026", "2.2.2026").replace("// Kommentar", "// anders"))
    check("Tabellen, Zeitstempel und Kommentare aendern die Signatur nicht", n1 == n2)
    n3 = DC.normalize_header(HEADER.replace("NUM_LEDS 20", "NUM_LEDS 21"))
    check("LED-Anzahl aendert die Signatur", n1 != n3)
    with tempfile.TemporaryDirectory() as t:
        sk = os.path.join(t, "Lib mit Ümlaut", "LEDs_AutoProg")
        os.makedirs(sk)
        with open(os.path.join(sk, "a.ino"), "w", encoding="utf-8") as fh:
            fh.write("int a;")
        h = os.path.join(sk, "LEDs_AutoProg.h")
        ini = os.path.join(t, "Lib mit Ümlaut", "platformio.ini")
        with open(ini, "w", encoding="utf-8") as fh:
            fh.write("; Created by x\n[env]\nlib_deps =\n    MobaLedLib=symlink://libraries/MobaLedLib@3.5.0\n")
        s1 = DC.compute_signature(HEADER, sk, h, os.path.dirname(sk), ini, "esp32")
        s2 = DC.compute_signature(HEADER, sk, h, os.path.dirname(sk), ini, "esp32")
        check("Signatur stabil, 16 Zeichen", s1 == s2 and len(s1) == DC.SIG_LEN)
        with open(os.path.join(sk, "a.ino"), "w", encoding="utf-8") as fh:
            fh.write("int a, b;")
        s3 = DC.compute_signature(HEADER, sk, h, os.path.dirname(sk), ini, "esp32")
        check("Aenderung einer Quelldatei aendert die Signatur", s3 != s1)
        check("andere Umgebung aendert die Signatur", DC.compute_signature(HEADER, sk, h, os.path.dirname(sk), ini, "pico") != s3)


# ---------------------------------------------------------------- Pfade
def test_paths():
    with tempfile.TemporaryDirectory() as t:
        d = os.path.join(t, "Ördner mit Leerzeichen")
        os.makedirs(os.path.join(d, "lib x"))
        sp = DC.short_path(d)
        check("short_path liefert einen vorhandenen Pfad", os.path.isdir(sp))
        if os.name == "nt":
            check("short_path: keine Leerzeichen/Umlaute (wenn 8.3 aktiv)", (" " not in sp and "Ö" not in sp) or sp == d)
        check("short_path: nicht vorhandener Pfad unveraendert", DC.short_path(os.path.join(d, "gibtsnicht")) == os.path.join(d, "gibtsnicht"))
        ini = "lib_deps =\n    A=symlink://lib x@3.5.0\n    B=file://%s\n    C=file://C:/JÃ¼rgen/none\n" % os.path.join(d, "lib x").replace("\\", "/")
        dirs = DC.ini_library_dirs(ini, d)
        check("ini: Pfad mit Leerzeichen/Umlaut gefunden, unbekannter ohne Absturz", len(dirs) == 2 and all(os.path.isdir(x) for x in dirs), dirs)


# ---------------------------------------------------------------- Konfigurationsdatei bauen (AVR-Werkzeuge)
MINI_H = """#include <Arduino.h>
#define MLL_DYNAMIC_CONFIG
//MLLDYN_BEGIN
#ifdef CONFIG_ONLY
const uint8_t Config[] __attribute__ ((section (".MLLLedConfig"))) = {1, 2, 3, 4, 5};
const uint16_t MLL_ConfigRamSize __attribute__ ((section (".MLLRamSize"))) = 7;
#define MLL_HAS_START_VALUES
typedef struct { uint16_t Channel; uint8_t Value; } __attribute__ ((packed)) Start_Value_T;
const Start_Value_T Start_Values_Tab[] __attribute__ ((section (".MLLStartConfig"))) = {{300, 1}, {301, 1}};
#endif
//MLLDYN_END
"""


def test_build():
    tools = DC.find_avr_tools([], [])
    if not tools:
        print("uebersprungen: keine AVR-Werkzeuge (Arduino15/PlatformIO) gefunden")
        return
    with tempfile.TemporaryDirectory() as t:
        sk = os.path.join(t, "Prüf Ordner mit Leerzeichen", "LEDs_AutoProg")
        os.makedirs(sk)
        with open(os.path.join(sk, "LEDs_AutoProg.h"), "w", encoding="utf-8") as fh:
            fh.write(MINI_H)
        lib = os.path.join(ROOT, "libraries", "MobaLedLib", "src")
        blob = DC.build_blob(sk, lib, tools, os.path.join(sk, "dyn"), SIG)
        head = DC.BLOB_HEADER.unpack(blob[:48])
        check("Bau im Pfad mit Umlaut/Leerzeichen: Laengen Config 5, Startwerte 6", head[4] == 5 and head[8] == 6, head)
        check("RAM-Groesse 7 und Signatur", head[3] == 7 and head[10].decode() == SIG)
        check("Nutzdaten: Config und Startwerte", blob[48:53] == bytes([1, 2, 3, 4, 5]) and blob[53:] == struct.pack("<HBHB", 300, 1, 301, 1))


# ---------------------------------------------------------------- Protokoll mit Ersatzgeraet
class FakeDevice:
    """Python-Nachbau des Protokolls aus LEDs_AutoProg/MLLDynConfig.h"""

    def __init__(self, sig, file=None):
        self.sig, self.file, self.out, self.inbuf, self.rx = sig, file, b"Programmmeldung\r\n", b"", None

    def open(self): pass
    def close(self): pass
    def flush(self): pass
    def reset_input_buffer(self): self.out = b""
    @property
    def in_waiting(self): return len(self.out)

    def read(self, n):
        d, self.out = self.out[:n], self.out[n:]
        return d

    def write(self, data):
        self.inbuf += data
        while b"\n" in self.inbuf:
            line, self.inbuf = self.inbuf.split(b"\n", 1)
            self.line(line.decode().strip())

    def say(self, s): self.out += (s + "\r\n").encode()
    def crc(self, b): return zlib.crc32(b) & 0xFFFFFFFF

    def line(self, line):
        if not line.startswith("~MLLCFG "):
            return
        line = line[8:]
        if line == "INFO":
            self.say("~MLLCFG INFO proto=2 sig=%s cfg=%08x valid=%d free=100000" % (self.sig, self.crc(self.file) if self.file else 0, 1 if self.file else 0))
        elif line.startswith("BEGIN "):
            _, size, crc = line.split()
            self.rx = dict(size=int(size), crc=int(crc, 16), pos=0, data=b"")
            self.say("~MLLCFG READY")
        elif line.startswith("DATA "):
            _, pos, hx = line.split(" ", 2)
            if not self.rx or int(pos) != self.rx["pos"]:
                return self.say("~MLLCFG ERR pos")
            b = bytes.fromhex(hx)
            self.rx["data"] += b
            self.rx["pos"] += len(b)
            self.say("~MLLCFG ACK %d" % self.rx["pos"])
        elif line == "END":
            r = self.rx
            if not r or r["pos"] != r["size"] or self.crc(r["data"]) != r["crc"] or r["data"][32:48].decode() != self.sig:
                return self.say("~MLLCFG ERR check")
            self.file = r["data"]
            self.say("~MLLCFG OK")
        else:
            self.say("~MLLCFG ERR cmd")


def test_protocol():
    blob = DC.pack_blob(bytes(range(49)), b"\x15\x40\x01", b"", b"", b"\x2c\x01\x01", 5, SIG)
    dev = FakeDevice(SIG)
    with mock.patch.object(serial, "Serial", lambda *a, **k: dev):
        link = DC.Link("COM9")
        info = DC.query_info(link, 3)
        check("INFO: Signatur und keine Datei", info and info["sig"] == SIG and info["valid"] == "0", info)
        DC.send_blob(link, blob)
        check("Datei im Geraet", dev.file == blob)
        info = DC.query_info(link, 3)
        check("INFO: CRC der Datei gleich", info["cfg"] == "%08x" % DC.blob_crc(blob) and info["valid"] == "1")
        big = DC.pack_blob(bytes(i % 251 for i in range(5000)), bytes(300), bytes(40), bytes(80), bytes(9), 123, SIG)
        DC.send_blob(link, big)
        check("grosse Datei in mehreren Teilen", dev.file == big)
    dev = FakeDevice("1111111111111111")
    with mock.patch.object(serial, "Serial", lambda *a, **k: dev):
        try:
            DC.send_blob(DC.Link("COM9"), blob)
            check("Datei fuer andere Firmware wird abgelehnt", False)
        except DC.DynConfigError:
            check("Datei fuer andere Firmware wird abgelehnt", dev.file is None)
    dev = FakeDevice("x")
    dev.line = lambda line: None
    with mock.patch.object(serial, "Serial", lambda *a, **k: dev):
        check("stummes Geraet: query_info liefert None", DC.query_info(DC.Link("COM9"), 2.5) is None)


# ---------------------------------------------------------------- Ausgabefenster
class FakePage:
    def __init__(self):
        self.lines, self.title, self.cleared = [], "", 0

    def add_text_to_textwindow(self, text="", nl="", highlight=None):
        self.lines.append((str(text).rstrip("\n"), highlight))

    def set_title(self, t): self.title = t
    def delete_text_from_textwindow(self): self.cleared += 1; self.lines.clear()
    def text(self): return "\n".join(l for l, _ in self.lines)


class FakeController:
    def __init__(self, page): self.page = page
    def getFramebyName(self, name): return self.page
    def showFramebyName(self, name): pass


def test_output():
    try:
        import proggen.M42_Dyn_Config as M42
    except Exception as e:                                  # noqa: BLE001
        print("uebersprungen: M42 nicht ladbar:", e)
        return
    blob = DC.pack_blob(bytes(i % 251 for i in range(5000)), bytes(300), bytes(40), bytes(80), bytes(9), 123, SIG)
    page = FakePage()
    M42._state.update(blob=blob, sig=SIG, pico=False, output=False)
    dev = FakeDevice(SIG)
    with mock.patch.object(M42.PG, "global_controller", FakeController(page), create=True), \
            mock.patch.object(serial, "Serial", lambda *a, **k: dev), mock.patch.object(M42.P01, "set_statusmessage", lambda *a, **k: None):
        check("schneller Weg: Rueckgabe True", M42.Try_Config_Only("COM9") is True)
        txt = page.text()
        check("Ausgabe: Pruefung der Firmware", "wird geprüft" in txt, txt)
        check("Ausgabe: nur die Konfiguration, Programm nicht neu", "nicht neu hochgeladen" in txt and "nur die Konfiguration" in txt, txt)
        check("Ausgabe: Fortschritt in Schritten bis 100 %", sum(1 for l, _ in page.lines if l.startswith("Konfiguration:")) in (4, 5) and "100 %" in txt, txt)
        check("Ausgabe: Fertigstellung gruen", page.lines[-1][1] == "OK" and "Fertig" in page.lines[-1][0], page.lines[-1])
        check("Ausgabe: Titel gesetzt, Merker fuer M08", "Konfiguration" in page.title and M42.Output_Written())
        check("Datei im Geraet", dev.file == blob)
        page.lines.clear()
        check("zweiter Lauf: schon aktuell", M42.Try_Config_Only("COM9") is True and "schon aktuell" in page.text(), page.text())
        dev.sig = "1111111111111111"
        page.lines.clear()
        check("andere Firmware: Rueckfall", M42.Try_Config_Only("COM9") is False)
        check("Ausgabe: Grund fuer das ganze Programm", "passt nicht" in page.text() and "ganze Programm" in page.text(), page.text())
        M42._state["output"] = False
        dev2 = FakeDevice(SIG)
        page.lines.clear()
    with mock.patch.object(M42.PG, "global_controller", FakeController(page), create=True), \
            mock.patch.object(serial, "Serial", lambda *a, **k: dev2), mock.patch.object(M42.P01, "set_statusmessage", lambda *a, **k: None), \
            mock.patch.object(DC, "wait_for_port", lambda *a, **k: "COM9"):
        check("nach dem Flashen: Rueckgabe True", M42.After_Full_Flash("COM9") is True)
        check("Ausgabe nach dem Flashen", "Programm ist hochgeladen" in page.text() and "100 %" in page.text() and page.lines[-1][1] == "OK", page.text())


# ---------------------------------------------------------------- Uebersetzung
def test_translation():
    try:
        sys.modules.setdefault("nicegui", mock.MagicMock())
        import _web.web_i18n as I
    except Exception as e:                                  # noqa: BLE001
        print("uebersprungen: web_i18n nicht ladbar:", e)
        return
    keys = ["Schnelles Update: nur geänderte Konfiguration übertragen (ESP32/Pico)",
            "Übertragen werden nur Änderungen an der Konfiguration, also Makros, Farben und Startwerte. Das dauert wenige Sekunden. Das Programm selbst wird nur beim ersten Mal oder nach Änderungen an Programm, Erweiterungen, LED-Anzahl oder Pins neu übertragen. Arduino Nano und Uno sind nicht betroffen. Nur mit PlatformIO und USB.",
            "Schnelles Update: Konfiguration übertragen",
            "Die Firmware im Gerät ({port}) wird geprüft ...",
            "Das Gerät antwortet nicht (noch nicht programmiert oder eine Firmware ohne diese Funktion). Es wird das ganze Programm hochgeladen.",
            "Die Firmware im Gerät passt nicht zu dieser Konfiguration. Es wird das ganze Programm hochgeladen.",
            "Die Firmware im Gerät passt. Das Programm wird nicht neu hochgeladen, es wird nur die Konfiguration übertragen ({n} Bytes).",
            "Die Konfiguration im Gerät ist schon aktuell. Es muss nichts übertragen werden.",
            "Konfiguration: {percent} % übertragen ({done} von {total} Bytes)",
            "Fertig: Die Konfiguration wurde in {seconds} s übertragen, das Gerät startet neu.",
            "Die Konfiguration konnte nicht übertragen werden ({reason}). Es wird das ganze Programm hochgeladen.",
            "Der Anschluss {port} lässt sich nicht öffnen ({reason}). Es wird das ganze Programm hochgeladen.",
            "Das Programm ist hochgeladen. Jetzt wird die Konfiguration übertragen ...",
            "Der Anschluss {port} erscheint nach dem Hochladen nicht wieder. Die Konfiguration wurde nicht übertragen.",
            "Der Anschluss {port} lässt sich nicht öffnen ({reason}). Die Konfiguration wurde nicht übertragen.",
            "Das Gerät antwortet nach dem Hochladen nicht. Die Konfiguration wurde nicht übertragen.",
            "Die Konfiguration wird übertragen ({n} Bytes) ...",
            "Die Konfiguration konnte nicht übertragen werden ({reason})."]
    for nr in range(0, 7):
        with I.use_language(nr):
            for k in keys:
                res = I.tr(k)
                check("Sprache %d: %s..." % (nr, k[:20]), (res == k) if nr == 0 else (res != k and len(res) > 10), res[:30])


if __name__ == "__main__":
    for f in (test_format, test_signature, test_paths, test_build, test_protocol, test_output, test_translation):
        try:
            f()
        except Exception as e:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(f.__name__ + " ohne Ausnahme", False, e)
    bad = [n for n, ok in Results if not ok]
    print("\n%d Pruefungen, %d Fehler" % (len(Results), len(bad)))
    sys.exit(1 if bad else 0)
