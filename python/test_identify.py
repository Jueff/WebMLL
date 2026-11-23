# Datei-Version: 1.00 (2026-11-23) - test_identify.py
# ----------------------------------------------------------------------------------------------
# Name:           test_identify.py
# Path:           test_identify.py
# Version:        1.00
# Last Update:    2026-11-23
# Author:         Jürgen Winkler
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-23  Neu: Test von M06.Write_Pico_Mainboard_LED_Defines (Identify, Pico): fehlende Mainboard_LED1..3 werden als SI_0 geschrieben,
#                     von der Tabelle definierte (auch D3/D4/D5) nicht; andere Boards schreiben nichts
# ----------------------------------------------------------------------------------------------
"""Aufruf: python test_identify.py
Die Funktion wird mit ast aus proggen/M06_Write_Header.py geholt (M06 selbst braucht die ganze Programmumgebung) und mit Ersatzobjekten ausgefuehrt.
Nicht geprueft: Firmware auf echter Hardware, der Rest von M06."""
import ast
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
failures = 0
checks = 0


def check(name, cond, info=""):
    global failures, checks
    checks += 1
    if cond:
        print("ok     " + name)
    else:
        failures += 1
        print("FEHLER " + name + (" - " + repr(info) if info else ""))


def load_function(name):
    path = os.path.join(HERE, "proggen", "M06_Write_Header.py")
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(src, fn)


class FakeFiles:
    def __init__(self):
        self.lines = []

    def writeText(self, fp, text, end):
        self.lines.append(text)


def run(board, config_txt):
    files = FakeFiles()
    m02 = types.SimpleNamespace(HT_PICO="PICO", HT_ESP32="ESP32", HT_NANO="NANO")
    m02a = types.SimpleNamespace(Get_BoardTyp=lambda: board)
    ns = {"VBFiles": files, "M02": m02, "M02a": m02a}
    exec(load_function("Write_Pico_Mainboard_LED_Defines"), ns)
    ns["Write_Pico_Mainboard_LED_Defines"](None, config_txt)
    return files.lines


def defined(lines):
    return [l.split()[1] for l in lines]


def test():
    out = run("PICO", "  RGB_Heartbeat(#LED)\r\n")
    check("Pico ohne eigene Defines: Mainboard_LED1..3 werden geschrieben", defined(out) == ["Mainboard_LED1", "Mainboard_LED2", "Mainboard_LED3"], out)
    check("Wert ist SI_0 (Eingangskanal immer 0), nicht der Pin", all(l.split()[2] == "SI_0" for l in out), out)

    cfg = "  // Mainboard_LED(1, SI_1)\r\n  #define Mainboard_LED1 SI_1                                     /* ... */\r\n  #define Mainboard_LED3 INCH_DCC_5_RED\r\n"
    out = run("PICO", cfg)
    check("Pico: von der Tabelle definierte LED 1 und 3 werden nicht noch einmal definiert", defined(out) == ["Mainboard_LED2"], out)

    out = run("PICO", "#define Mainboard_LED_D4 5\r\n")
    check("Pico: alter Name Mainboard_LED_D4 zaehlt als LED 2", defined(out) == ["Mainboard_LED1", "Mainboard_LED3"], out)

    out = run("PICO", "#define Mainboard_LED13 5\r\n#define Mainboard_LED10 SI_1\r\n")
    check("Pico: Mainboard_LED13 oder 10 zaehlt nicht als LED 1", defined(out) == ["Mainboard_LED1", "Mainboard_LED2", "Mainboard_LED3"], out)

    out = run("PICO", "// #define Mainboard_LED1 5   (Kommentar)\r\n")
    check("Pico: auskommentierte Zeile zaehlt nicht", defined(out) == ["Mainboard_LED1", "Mainboard_LED2", "Mainboard_LED3"], out)

    out = run("PICO", "#define Mainboard_LED1 SI_1\r\n#define Mainboard_LED2 SI_1\r\n#define Mainboard_LED3 SI_1\r\n")
    check("Pico: alle drei in der Tabelle: nichts schreiben", out == [], out)

    for board in ("ESP32", "NANO"):
        check("%s: nichts schreiben" % board, run(board, "") == [])


if __name__ == "__main__":
    test()
    print("\n%d Pruefungen, %d Fehler" % (checks, failures))
    sys.exit(1 if failures else 0)
