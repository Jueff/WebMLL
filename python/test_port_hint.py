# Datei-Version: 1.00 (2026-11-26) - test_port_hint.py
# ----------------------------------------------------------------------------------------------
# Name:           test_port_hint.py
# Path:           test_port_hint.py
# Version:        1.00
# Last Update:    2026-11-26
# Author:         Jürgen Winkler
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-26  Neu: negative Zahl im Anschluss (-3 = Hinweis COM3) beim Hochladen und beim Setup uebertragen (M07_COM_Port 1.20: Resolve_Port_Hint)
# ----------------------------------------------------------------------------------------------
"""Aufruf: python test_port_hint.py

Startet die echte Arbeitsmappe ohne Oberflaeche (wie test_protocol_switch.py) und prueft, dass eine negative Zahl im Anschluss der Lichtmaschine als Hinweis dient:
Ist COM<n> am Rechner vorhanden und passt der Typ des Geraets zum Blatt, wird COM<n> ins Blatt eingetragen; sonst bleibt der Anschluss ungueltig und der Anwender
muss das Geraet erkennen lassen (Dialog). Die Anschlussliste des Rechners wird ersetzt. Nur unter Windows (dort steht die Zahl fuer COM<n>)."""
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ["MLL_HEADLESS"] = "1"
os.environ["MLL_DATA_DIR"] = tempfile.mkdtemp(prefix="mll_test_")
sys.path.insert(0, ROOT)
os.chdir(ROOT)


def port(device, kind):
    """Anschluss wie pyserial ihn liefert: Nano (CH340), ESP32 (CP210x) oder Pico (VID 2E8A)"""
    return {"Nano": SimpleNamespace(device=device, description="USB-SERIAL CH340 (%s)" % device, hwid="USB VID:PID=1A86:7523", vid=0x1A86),
            "ESP32": SimpleNamespace(device=device, description="Silicon Labs CP210x USB to UART Bridge (%s)" % device, hwid="USB VID:PID=10C4:EA60", vid=0x10C4),
            "Pico": SimpleNamespace(device=device, description="USB Serial Device (%s)" % device, hwid="USB VID:PID=2E8A:000A", vid=0x2E8A)}[kind]


@unittest.skipUnless(os.name == "nt", "Hinweis COM<n> gilt nur unter Windows")
class PortHintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import no_tk
        no_tk.install()
        from headless.headless_app_controller import HeadlessAppController
        import userdata
        ctrl = HeadlessAppController(mainfile_dir=ROOT, command_line_args={"loaddatafile": "True", "logfilename": userdata.log_file()})
        ctrl.create_excel_application()
        from headless.headless_proggen import HeadlessProgGeneratorPage
        cls.wb = HeadlessProgGeneratorPage(ctrl).workbook
        import proggen.M02_Public as M02
        import proggen.M07_COM_Port as M07
        import proggen.M07_COM_Port_New as M07New
        import proggen.M25_Columns as M25
        cls.M02, cls.M07, cls.M07New, cls.M25 = M02, M07, M07New, M25

    def setUp(self):
        self.ws = next(s for s in self.wb.sheets if s.Name == "DCC")        # Standardblatt: Nano
        self.ws.Activate()
        self.M25.Col_from_Sheet = ""
        self.M25.Make_sure_that_Col_Variables_match(self.ws)
        self.col = self.M25.COMPort_COL
        self.saved_port = str(self.ws.Cells(self.M02.SH_VARS_ROW, self.col).Value or "")
        self.original = self.M07.portlist.comports
        self.dialogs = []
        self.original_dialog = self.M07New.USB_Port_Dialog
        self.M07New.USB_Port_Dialog = lambda column: self.dialogs.append(column) or False

    def tearDown(self):
        self.M07.portlist.comports = self.original
        self.M07New.USB_Port_Dialog = self.original_dialog
        self.ws.CellDict[self.M02.SH_VARS_ROW, self.col] = self.saved_port

    def attached(self, *ports):
        self.M07.portlist.comports = lambda include_links=False: list(ports)

    def cell(self):
        return str(self.ws.Cells(self.M02.SH_VARS_ROW, self.col)).strip()

    def set_cell(self, value):
        self.ws.CellDict[self.M02.SH_VARS_ROW, self.col] = value

    def test_hint_number(self):
        for value, number in (("-3", 3), ("*-12", 12), ("COM3", 0), ("3", 0), ("", 0), ("-", 0), ("COM?", 0)):
            self.set_cell(value)
            self.assertEqual(self.M07.Port_Hint_Number(self.col), number, value)

    def test_hint_found_enters_port(self):
        self.set_cell("-3")
        self.attached(port("COM3", "Nano"))
        self.assertTrue(self.M07.Check_USB_Port_with_Dialog(self.col))
        self.assertEqual(self.cell(), "COM3")
        self.assertEqual(self.dialogs, [])

    def test_hint_other_device_at_port_needs_detection(self):
        self.set_cell("-3")
        self.attached(port("COM3", "ESP32"), port("COM4", "Nano"))              # am Hinweis-Anschluss haengt ein ESP32, das Blatt ist ein Nano
        self.assertFalse(self.M07.Check_USB_Port_with_Dialog(self.col))
        self.assertEqual(self.cell(), "-3")
        self.assertEqual(self.dialogs, [self.col])                             # der Anwender muss das Geraet erkennen lassen

    def test_hint_port_missing_needs_detection(self):
        self.set_cell("-3")
        self.attached(port("COM5", "Nano"))
        self.assertFalse(self.M07.Check_USB_Port_with_Dialog(self.col))
        self.assertEqual(self.cell(), "-3")
        self.assertEqual(self.dialogs, [self.col])

    def test_ensure_with_hint_does_not_take_another_board(self):
        self.set_cell("-3")
        self.attached(port("COM5", "Nano"))                                     # genau ein passendes Board, aber an einem anderen Anschluss
        self.assertEqual(self.M07.Ensure_Existing_USB_Port(self.col), "")
        self.assertEqual(self.cell(), "-3")
        self.attached(port("COM3", "Nano"), port("COM5", "Nano"))
        self.assertEqual(self.M07.Ensure_Existing_USB_Port(self.col), "COM3")
        self.assertEqual(self.cell(), "COM3")

    def test_without_hint_single_board_is_still_taken(self):
        self.set_cell("COM9")                                                   # kein Hinweis: bisheriges Verhalten (genau ein passendes Board)
        self.attached(port("COM5", "Nano"))
        self.assertEqual(self.M07.Ensure_Existing_USB_Port(self.col), "COM5")


if __name__ == "__main__":
    unittest.main(verbosity=2)
