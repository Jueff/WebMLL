# Datei-Version: 1.00 (2026-11-26) - test_pico_device_dialog.py
# ----------------------------------------------------------------------------------------------
# Name:           test_pico_device_dialog.py
# Path:           test_pico_device_dialog.py
# Version:        1.00
# Last Update:    2026-11-26
# Author:         Jürgen Winkler
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-26  Neu: Geraeteauswahl fuer die Firmware-Installation des Pico (web_form_comport 1.45, _fw_mode): nur Pico-Geraete, auch unbekannte und andere MobaLedLib Geraete
# ----------------------------------------------------------------------------------------------
"""Aufruf: python test_pico_device_dialog.py

Prueft die Regeln der Geraeteauswahl im Firmware-Modus ohne Browser: Liste (nur Pico-Geraete, Servo-Module waehlbar), Blatt und Build Optionen bleiben unveraendert.
Die Anschlussliste des Rechners wird ersetzt, es wird kein Anschluss geoeffnet."""
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


def port(device, vid, desc, pid=0x0001, serial=""):
    return SimpleNamespace(device=device, description=desc, hwid="USB VID:PID=%04X:%04X" % (vid, pid), vid=vid, pid=pid, serial_number=serial)


PORTS = [port("COM3", 0x1A86, "USB-SERIAL CH340 (COM3)", 0x7523),                 # Nano
         port("COM4", 0x10C4, "Silicon Labs CP210x USB to UART Bridge (COM4)", 0xEA60),  # ESP32
         port("COM5", 0x2E8A, "USB Serial Device (COM5)", 0x000A, "E661"),         # Pico
         port("COM6", 0x2E8A, "USB Serial Device (COM6)", 0x000A, "E662"),         # Pico, spaeter als Servo-Modul erkannt
         port("COM7", 0x0403, "FTDI Geraet (COM7)", 0x6001),                        # FTDI: gilt als Nano
         port("COM8", 0x1234, "Mystery Device (COM8)", 0x0001)]                    # keinem Typ zuzuordnen


class FirmwareDeviceTests(unittest.TestCase):
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
        import proggen.F00_mainbuttons as F00
        import proggen.M07_COM_Port as M07
        import proggen.M07_COM_Port_New as M07New
        cls.F00, cls.M07, cls.M07New = F00, M07, M07New

    def setUp(self):
        self.form = self.F00.Select_COM_Port_UserForm
        self.original = self.M07.portlist.comports
        self.M07.portlist.comports = lambda include_links=False: list(PORTS)
        self.saved = (self.M07New.Ident_Send_Keepalive, self.M07New._Ident_Post)
        self.M07New.Ident_Send_Keepalive = lambda *a, **k: None
        self.M07New._Ident_Post = lambda *a, **k: None
        self.form._info_refresh = lambda *a, **k: None                        # keine Abfrage ueber die Anschluesse
        self.form._info, self.form._boot, self.form._boot_busy = {}, {}, set()
        self.form._rows, self.form._sel_dev, self.form._prev_devs, self.form._old_comport = [], None, None, None
        self.form._stored_port = ""
        self.form._show_unknown = False
        self.form._fw_mode = True

    def tearDown(self):
        self.form._fw_mode = False
        self.M07.portlist.comports = self.original
        self.M07New.Ident_Send_Keepalive, self.M07New._Ident_Post = self.saved
        self.M07.SERVO_PORTS.pop("COM6", None)

    def test_only_pico_devices_are_listed(self):
        self.form._compute_new()
        self.assertEqual([r["dev"] for r in self.form._rows], ["COM5", "COM6"])        # Nano, ESP32 und das unbekannte Geraet fehlen
        self.assertEqual({r["typ"] for r in self.form._rows}, {"Pico"})

    def test_unknown_ports_with_checkbox(self):
        self.form._show_unknown = True                                                 # das Kontrollkaestchen ist in der Firmware-Auswahl von Anfang an aktiv
        self.form._compute_new()
        rows = {r["dev"]: r["typ"] for r in self.form._rows}
        self.assertEqual(rows, {"COM5": "Pico", "COM6": "Pico", "COM8": "unbekannt"})  # Nano und ESP32 bleiben ausgeschlossen
        self.assertTrue(all(self.form._is_selectable(r) for r in self.form._rows))

    def test_no_image_for_other_mobaledlib_devices(self):
        self.M07.SERVO_PORTS["COM6"] = "Servo"
        self.form._compute_new()
        self.form._sel_dev = "COM5"
        self.assertTrue(self.form._board_view()["image"])                              # Pico: Bild
        self.form._sel_dev = "COM6"
        self.assertEqual(self.form._board_view()["image"], "")                         # Andere MobaLedLib Geraete: kein Bild

    def test_other_mobaledlib_devices_are_selectable(self):
        self.M07.SERVO_PORTS["COM6"] = "Servo"                                         # als Servo-Modul erkannt
        self.form._compute_new()
        rows = {r["dev"]: r for r in self.form._rows}
        self.assertEqual(rows["COM6"]["typ"], "Servo")
        self.assertTrue(self.form._is_selectable(rows["COM6"]))
        self.form._fw_mode = False
        self.assertFalse(self.form._is_selectable(rows["COM6"]))                       # als Lichtmaschine bleibt es gesperrt

    def test_stored_port_that_is_gone_is_not_listed(self):
        self.form._stored_port = "COM9"
        self.form._compute_new()
        self.assertNotIn("COM9", [r["dev"] for r in self.form._rows])

    def test_sheet_is_not_touched(self):
        self.assertEqual(self.form._sheet_group(), "Pico")
        self.assertFalse(self.form._apply_group("Classic"))
        self.assertFalse(self.form._apply_group("Pro"))

    def test_placeholder_port_is_no_device(self):
        for value in ("COM?", "NO DEVICE", "999", "-3", "", None):
            self.assertEqual(self.form._norm_port(value), "", value)
        self.assertEqual(self.form._norm_port("COM3"), "COM3")
        self.form._fw_mode = False
        self.M07.portlist.comports = lambda include_links=False: []           # kein Geraet angeschlossen
        self.form._stored_port = self.form._norm_port("COM?")
        self.form._compute_new()
        self.assertEqual(self.form._rows, [])                                 # keine Zeile COM?
        self.assertIsNone(self.form._sel_dev)                                 # nichts gewaehlt

    def test_normal_mode_is_unchanged(self):
        self.form._fw_mode = False
        self.form._compute_new()
        devs = [r["dev"] for r in self.form._rows]
        self.assertIn("COM3", devs)
        self.assertIn("COM4", devs)
        self.assertIn("COM5", devs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
