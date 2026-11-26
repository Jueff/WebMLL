# Datei-Version: 1.00 (2026-11-26) - test_monitor_connect.py
# ----------------------------------------------------------------------------------------------
# Name:           test_monitor_connect.py
# Path:           test_monitor_connect.py
# Version:        1.00
# Last Update:    2026-11-26
# Author:         Jürgen Winkler
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-26  Neu: Serial Monitor verbindet nur zum Mitlesen (web_serial 1.22, connect_monitor): keine Abfrage am Geraet
# ----------------------------------------------------------------------------------------------
"""Aufruf: python test_monitor_connect.py

Prueft mit einer gefaelschten seriellen Schnittstelle, dass der Serial Monitor das Geraet nicht abfragt: es wird nichts gesendet ('#?', '#X'), der Fehlerdialog
'Falsche oder keine Antwort vom Geraet' kommt nicht, auch wenn das Geraet nie antwortet; connect() (zentraler Knopf) fragt dagegen weiter ab."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ["MLL_HEADLESS"] = "1"
os.environ["MLL_DATA_DIR"] = tempfile.mkdtemp(prefix="mll_test_")
sys.path.insert(0, ROOT)
os.chdir(ROOT)


class FakeSerial:
    """Ein Geraet, das nie antwortet; merkt sich, was ihm gesendet wurde"""
    def __init__(self):
        self.written, self.closed, self.in_waiting = [], False, 0

    def write(self, data):
        self.written.append(bytes(data))
        return len(data)

    def flush(self):
        pass

    def read(self, n=1):
        return b""

    def close(self):
        self.closed = True

    def reset_input_buffer(self):
        pass

    def readline(self):
        return b""


class MonitorConnectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import no_tk
        no_tk.install()
        from headless.headless_app_controller import HeadlessAppController
        import userdata
        cls.ctrl = HeadlessAppController(mainfile_dir=ROOT, command_line_args={"loaddatafile": "True", "logfilename": userdata.log_file()})
        cls.ctrl.create_excel_application()

    def setUp(self):
        c = self.ctrl
        self.fake = FakeSerial()
        self.messages = []
        self.saved = (c._open_serial, c._start_reader, c._msg, c.send_to_ARDUINO, c.send_to_ARDUINO_init_buffer, c._wait_sent)
        c._open_serial = lambda serial, port: self.fake
        c._start_reader = lambda: None
        c._msg = lambda text, title="", *a, **k: self.messages.append((title, text)) or 6
        self.sent = []
        c.send_to_ARDUINO = lambda text, *a, **k: self.sent.append(text)
        c.send_to_ARDUINO_init_buffer = lambda *a, **k: None
        c._wait_sent = lambda *a, **k: None
        c.arduino = None
        c.ARDUINO_current_portname = ""

    def tearDown(self):
        c = self.ctrl
        (c._open_serial, c._start_reader, c._msg, c.send_to_ARDUINO, c.send_to_ARDUINO_init_buffer, c._wait_sent) = self.saved
        c.arduino = None
        c.ARDUINO_current_portname = ""

    def test_monitor_connect_sends_nothing_and_shows_no_error(self):
        self.assertTrue(self.ctrl.connect_monitor("COM77"))
        self.assertEqual(self.sent, [])                                          # kein '#?', kein '#X'
        self.assertEqual(self.fake.written, [])
        self.assertEqual(self.messages, [])                                      # kein Dialog 'Falsche oder keine Antwort'
        self.assertEqual(self.ctrl.ARDUINO_current_portname, "COM77")
        text, fg = self.ctrl.connect_status
        self.assertIn("COM77", text)
        self.assertEqual(fg, "green")
        self.assertFalse(getattr(self.ctrl, "monitor_only", False))             # gilt nur fuer diesen Aufruf

    def test_monitor_connect_can_open_error_gives_message(self):
        def fail(serial, port):
            raise OSError("Zugriff verweigert")
        self.ctrl._open_serial = fail
        self.assertFalse(self.ctrl.connect_monitor("COM78"))
        self.assertEqual(len(self.messages), 1)
        self.assertIn("COM78", self.messages[0][1])

    def test_dtr_follows_the_device_at_the_port_not_the_board_of_the_sheet(self):
        from types import SimpleNamespace
        from serial.tools import list_ports
        ports = [SimpleNamespace(device="COM81", vid=0x2E8A, pid=0x000A, description="USB Serial Device", hwid="USB VID:PID=2E8A:000A"),     # Pico
                 SimpleNamespace(device="COM82", vid=0x10C4, pid=0xEA60, description="CP210x", hwid="USB VID:PID=10C4:EA60"),                 # ESP32
                 SimpleNamespace(device="COM83", vid=0x1A86, pid=0x7523, description="USB-SERIAL CH340", hwid="USB VID:PID=1A86:7523"),      # Nano
                 SimpleNamespace(device="COM84", vid=0x9999, pid=0x0001, description="Mystery", hwid="USB VID:PID=9999:0001")]               # unbekannt
        seen = {}

        def open_serial(serial, port):
            seen[port] = self.ctrl._board_needs_dtr()
            return self.fake
        self.ctrl._open_serial = open_serial
        orig = list_ports.comports
        list_ports.comports = lambda *a, **k: ports
        orig_board = self.ctrl.dtr_override
        try:
            for port in ("COM81", "COM82", "COM83", "COM84"):
                self.ctrl.arduino = None
                self.ctrl.ARDUINO_current_portname = ""
                self.assertTrue(self.ctrl.connect_monitor(port))
            self.assertTrue(seen["COM81"])                                       # Pico: DTR an, auch wenn im Blatt ein anderes Board steht
            self.assertFalse(seen["COM82"])                                      # ESP32: DTR aus
            self.assertFalse(seen["COM83"])                                      # Nano: DTR aus
            self.assertEqual(seen["COM84"], self.ctrl._board_needs_dtr())        # unbekannt: Board im Blatt
            self.assertEqual(self.ctrl.dtr_override, orig_board)                 # gilt nur fuer diesen Aufruf
        finally:
            list_ports.comports = orig

    def test_normal_connect_still_queries_the_device(self):
        import time
        orig_sleep = time.sleep
        time.sleep = lambda s: orig_sleep(min(s, 0.001))                          # den Handshake nicht in Echtzeit abwarten
        try:
            start = time.time()
            ok = self.ctrl.connect("COM79")
        finally:
            time.sleep = orig_sleep
        self.assertFalse(ok)                                                     # das Geraet antwortet nie
        self.assertIn("#?\r\n", self.sent)                                       # der zentrale Weg fragt ab
        self.assertTrue(any("Falsche oder keine Antwort" in m[1] for m in self.messages))


if __name__ == "__main__":
    unittest.main(verbosity=2)
