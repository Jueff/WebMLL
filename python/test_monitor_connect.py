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
