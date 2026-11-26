# Datei-Version: 1.00 (2026-11-26) - test_single_connection.py
# ----------------------------------------------------------------------------------------------
# Name:           test_single_connection.py
# Path:           test_single_connection.py
# Version:        1.00
# Last Update:    2026-11-26
# Author:         Jürgen Winkler
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-26  Neu: Tests fuer 'eine Verbindung pro Geraet' (web_serial 1.20): parallele connect-Aufrufe, Wiederverwendung (USB, WLAN-Adresse), connect_silent,
#                     Anschluss-Sperre gegenueber Abfragen, kein Deadlock bei gegenlaeufiger Reihenfolge
# ----------------------------------------------------------------------------------------------
"""Aufruf: python test_single_connection.py

Benutzt die echten Funktionen von _web/web_serial.py (SerialMixin). Ersetzt werden nur das Modul serial (ein Ersatz-Anschluss, der wie Windows ein zweites Oeffnen mit
PermissionError ablehnt und auf '#?' mit der Startmeldung antwortet) und die Oberflaeche (Meldungen, Konfiguration).
Nicht geprueft: echte Hardware, M07_COM_Port_New (braucht die Excel-Schicht), Oberflaeche."""
import os
import sys
import threading
import time
import types
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

STARTMSG = b"#?LEDs_AutoProg Ver 3: PICO 3.5.0-L3 26.11.26 09:22,26\r\n"


class FakeWorld:
    """Merkt, welche Anschluesse offen sind und wie oft geoeffnet wurde."""

    def __init__(self):
        self.lock = threading.Lock()
        self.open_ports = set()
        self.open_count = {}
        self.max_open_at_once = 0
        self.permission_errors = 0
        self.open_delay = 0.0


WORLD = FakeWorld()


class FakeSerial:
    PARITY_NONE, STOPBITS_ONE, EIGHTBITS = "N", 1, 8

    def __init__(self, *a, **k):
        self.port = None
        self.baudrate = 115200
        self.timeout = 0
        self.dtr = True
        self.rts = True
        self.is_open = False
        self._buf = bytearray()
        self.portstr = ""

    def open(self):
        time.sleep(WORLD.open_delay)
        with WORLD.lock:
            if self.port in WORLD.open_ports:                    # Windows: zweites Oeffnen -> PermissionError(13)
                WORLD.permission_errors += 1
                raise PermissionError(13, "Zugriff verweigert", self.port)
            WORLD.open_ports.add(self.port)
            WORLD.open_count[self.port] = WORLD.open_count.get(self.port, 0) + 1
            WORLD.max_open_at_once = max(WORLD.max_open_at_once, len(WORLD.open_ports))
        self.is_open = True
        self.portstr = self.port

    @property
    def in_waiting(self):
        return len(self._buf)

    def read(self, n=1):
        if not self._buf:
            time.sleep(0.005)
            return b""
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def write(self, data):
        if b"#?" in bytes(data) or bytes(data) == b"?":          # die Lichtmaschine antwortet auf '#?' (auch Zeichen fuer Zeichen gesendet)
            self._tail = getattr(self, "_tail", b"") + bytes(data)
            if b"#?" in self._tail:
                self._tail = b""
                self._buf.extend(STARTMSG)
        elif bytes(data) == b"#":
            self._tail = b"#"
        else:
            self._tail = b""
        return len(data)

    def flush(self):
        pass

    def reset_input_buffer(self):
        self._buf.clear()

    def close(self):
        if self.is_open:
            self.is_open = False
            with WORLD.lock:
                WORLD.open_ports.discard(self.port)


fake_serial = types.ModuleType("serial")
fake_serial.Serial = FakeSerial
fake_serial.PARITY_NONE, fake_serial.STOPBITS_ONE, fake_serial.EIGHTBITS = "N", 1, 8
fake_tools = types.ModuleType("serial.tools")  # Unterpakete, damit andere Module (Excel-Schicht) beim Import nicht scheitern
fake_ports = types.ModuleType("serial.tools.list_ports")
fake_ports.comports = lambda include_links=False: []
fake_tools.list_ports = fake_ports
fake_serial.tools = fake_tools
sys.modules["serial"] = fake_serial
sys.modules["serial.tools"] = fake_tools
sys.modules["serial.tools.list_ports"] = fake_ports

from _web import web_serial  # noqa: E402


class Ctl(web_serial.SerialMixin):
    """Kleinster Controller um den echten SerialMixin"""

    def __init__(self, ip_open=None):
        self._serial_init()
        self.status = []
        self.cfg = {"serportname": "COM7", "ARDUINO_WAITTIME": 0.0}
        self.maxled = 20
        self.MacroDef = None
        self.dtr_seen = []

    def getConfigData(self, key):
        return self.cfg.get(key, "")

    def setConfigData(self, key, value):
        self.cfg[key] = value

    def set_connectstatusmessage(self, text, fg="black"):
        self.status.append(text)

    def set_maxLEDcnt(self, n):
        self.maxled = n

    def get_maxLEDcnt(self):
        return self.maxled

    def _board_needs_dtr(self):
        self.dtr_seen.append(self.dtr_override)
        return bool(self.dtr_override)

    def led_off(self):
        pass


def fresh():
    WORLD.__init__()
    return Ctl()


class SingleConnection(unittest.TestCase):
    def test_parallel_connect_opens_once(self):
        """Zehn Threads verbinden gleichzeitig mit COM7: der Anschluss wird genau einmal geoeffnet, kein PermissionError."""
        ctl = fresh()
        WORLD.open_delay = 0.05
        results, errors = [], []

        def run():
            try:
                results.append(ctl.connect(port="COM7", wlan=False))
            except Exception as ex:                               # noqa: BLE001
                errors.append(ex)
        ts = [threading.Thread(target=run) for _ in range(10)]
        [t.start() for t in ts]
        [t.join(30) for t in ts]
        self.assertFalse(errors, errors)
        self.assertEqual(results, [True] * 10)
        self.assertEqual(WORLD.open_count.get("COM7"), 1)
        self.assertEqual(WORLD.permission_errors, 0)
        self.assertTrue(ctl.is_connection_open())
        self.assertEqual(ctl.ARDUINO_current_portname, "COM7")
        ctl.disconnect()

    def test_connect_twice_reuses(self):
        ctl = fresh()
        self.assertTrue(ctl.connect(port="COM7", wlan=False))
        first = ctl.arduino
        self.assertTrue(ctl.connect(port="COM7", wlan=False))
        self.assertIs(ctl.arduino, first)
        self.assertEqual(WORLD.open_count["COM7"], 1)
        ctl.disconnect()

    def test_other_port_replaces(self):
        ctl = fresh()
        self.assertTrue(ctl.connect(port="COM7", wlan=False))
        self.assertTrue(ctl.connect(port="COM8", wlan=False))
        self.assertEqual(ctl.ARDUINO_current_portname, "COM8")
        self.assertNotIn("COM7", WORLD.open_ports)
        ctl.disconnect()

    def test_connect_if_not_connected_waits_for_connect_in_progress(self):
        """Ein zweiter Aufrufer sieht die halbfertige Verbindung (arduino gesetzt, Handshake laeuft) nicht als verbunden."""
        ctl = fresh()
        WORLD.open_delay = 0.2
        res = {}
        t = threading.Thread(target=lambda: res.setdefault("a", ctl.connect(port="COM7", wlan=False)))
        t.start()
        time.sleep(0.1)
        ok = ctl.connect_if_not_connected(port="COM7")
        t.join(30)
        self.assertTrue(ok)
        self.assertEqual(ctl.ARDUINO_current_portname, "COM7")      # beim Rueckkehren ist der Handshake abgeschlossen
        self.assertEqual(WORLD.open_count["COM7"], 1)
        ctl.disconnect()

    def test_silent_connect_keeps_open_connection(self):
        ctl = fresh()
        self.assertTrue(ctl.connect(port="COM7", wlan=False))
        first = ctl.arduino
        self.assertTrue(ctl.connect_silent(port="COM8", wlan=False, dtr=True))
        self.assertIs(ctl.arduino, first)                            # keine zweite Verbindung, die offene bleibt
        self.assertEqual(WORLD.open_count.get("COM8"), None)
        self.assertFalse(ctl.quiet)
        self.assertIsNone(ctl.dtr_override)
        ctl.disconnect()

    def test_silent_connect_resets_attributes_and_dtr(self):
        ctl = fresh()
        self.assertTrue(ctl.connect_silent(port="COM7", wlan=False, dtr=True))
        self.assertIn(True, ctl.dtr_seen)                            # dtr_override galt waehrend des Verbindens
        self.assertFalse(ctl.quiet)
        self.assertIsNone(ctl.dtr_override)
        ctl.disconnect()

    def test_silent_connect_verify_disconnects(self):
        ctl = fresh()
        self.assertFalse(ctl.connect_silent(port="COM7", wlan=False, verify=lambda: False))
        self.assertFalse(ctl.is_connection_open())
        self.assertNotIn("COM7", WORLD.open_ports)

    def test_parallel_silent_and_normal_connect(self):
        """Autoconnect (still) und Knopf (normal) gleichzeitig: eine Verbindung, danach quiet=False."""
        ctl = fresh()
        WORLD.open_delay = 0.05
        out = []
        ts = [threading.Thread(target=lambda: out.append(ctl.connect_silent(port="COM7", wlan=False))),
              threading.Thread(target=lambda: out.append(ctl.connect(port="COM7", wlan=False))),
              threading.Thread(target=lambda: out.append(ctl.connect_silent(port="COM7", wlan=False, dtr=True)))]
        [t.start() for t in ts]
        [t.join(30) for t in ts]
        self.assertEqual(out, [True] * 3)
        self.assertEqual(WORLD.open_count["COM7"], 1)
        self.assertEqual(WORLD.permission_errors, 0)
        self.assertFalse(ctl.quiet)
        ctl.disconnect()

    def test_startmessage_evaluated_once_per_connection(self):
        ctl = fresh()
        calls = []
        orig = ctl.set_maxLEDcnt
        ctl.set_maxLEDcnt = lambda n: (calls.append(n), orig(n))
        ctl.connect(port="COM7", wlan=False)
        self.assertEqual(len(calls), 1)                              # RxLog.on_line und Handshake: nur eine Auswertung
        ctl.disconnect()
        ctl.connect(port="COM7", wlan=False)
        self.assertEqual(len(calls), 2)                              # neue Verbindung, neue Auswertung
        ctl.disconnect()

    def test_port_lock_excludes_connect_handshake(self):
        """Eine Abfrage (haelt die Anschluss-Sperre) laeuft nie gleichzeitig mit dem Oeffnen: connect wartet."""
        ctl = fresh()
        order = []
        got = threading.Event()

        def query():
            with web_serial.PORT_ACCESS_LOCK:
                got.set()
                order.append("query_start")
                time.sleep(0.3)
                order.append("query_end")
        tq = threading.Thread(target=query)
        tq.start()
        got.wait(5)
        t0 = time.monotonic()
        ctl.connect(port="COM7", wlan=False)
        waited = time.monotonic() - t0
        order.append("connected")
        tq.join(5)
        self.assertEqual(order, ["query_start", "query_end", "connected"])
        self.assertGreaterEqual(waited, 0.25)
        ctl.disconnect()

    def test_no_deadlock_opposite_order(self):
        """Verbinden (conn_lock, dann Anschluss-Sperre) und eine Abfrage (nur Anschluss-Sperre) gleichzeitig, viele Runden: kein Stillstand."""
        ctl = fresh()
        stop = time.monotonic() + 3
        errors = []

        def connector():
            try:
                while time.monotonic() < stop:
                    ctl.connect(port="COM7", wlan=False)
                    ctl.disconnect()
            except Exception as ex:                               # noqa: BLE001
                errors.append(ex)

        def querier():
            try:
                while time.monotonic() < stop:
                    with web_serial.PORT_ACCESS_LOCK:
                        time.sleep(0.001)
                        ctl.close_arduino_connection_after_write_error(expected_port=object(), lock_timeout=0)   # wie _Release_Main_Connection
            except Exception as ex:                               # noqa: BLE001
                errors.append(ex)
        ts = [threading.Thread(target=connector), threading.Thread(target=connector), threading.Thread(target=querier)]
        [t.start() for t in ts]
        [t.join(15) for t in ts]
        self.assertFalse([t for t in ts if t.is_alive()], "Deadlock")
        self.assertFalse(errors, errors)
        self.assertEqual(WORLD.permission_errors, 0)

    def test_close_after_write_error_waits_for_conn_lock_with_timeout(self):
        ctl = fresh()
        ctl.connect(port="COM7", wlan=False)
        port = ctl.arduino
        holder_has = threading.Event()
        release = threading.Event()

        def hold():
            with ctl._conn_lock:
                holder_has.set()
                release.wait(5)
        t = threading.Thread(target=hold)
        t.start()
        holder_has.wait(5)
        t0 = time.monotonic()
        ctl.close_arduino_connection_after_write_error(expected_port=port, lock_timeout=0.2)   # kommt nicht an die Sperre: schliesst nach dem Timeout trotzdem
        self.assertLess(time.monotonic() - t0, 2)
        self.assertFalse(ctl.is_connection_open())
        release.set()
        t.join(5)

    def test_wlan_reuse(self):
        """connect_esp32 / connectIP mit derselben Adresse: kein Trennen und Neuverbinden."""
        ctl = fresh()
        ctl.arduino = types.SimpleNamespace(is_open=True, portstr="10.0.0.5", close=lambda: None)
        ctl.ARDUINO_IP = True
        ctl.ARDUINO_current_portname = "10.0.0.5"
        called = []
        ctl._connectIP_impl = lambda *a, **k: called.append(a) or True
        self.assertTrue(ctl.connect_esp32("10.0.0.5", "pw"))
        self.assertTrue(ctl.connectIP("10.0.0.5"))
        self.assertEqual(called, [])                                 # nichts neu aufgebaut
        self.assertTrue(ctl.connect_esp32("10.0.0.6", "pw"))         # andere Adresse: neu
        self.assertEqual(len(called), 1)

    def test_connect_via_ip_port_string_reuses(self):
        ctl = fresh()
        ctl.arduino = types.SimpleNamespace(is_open=True, portstr="10.0.0.5", close=lambda: None)
        ctl.ARDUINO_IP = True
        ctl.ARDUINO_current_portname = "10.0.0.5"
        called = []
        ctl._connectIP_impl = lambda *a, **k: called.append(a) or True
        self.assertTrue(ctl.connect(port="IP:10.0.0.5", wlan=False))
        self.assertEqual(called, [])
        self.assertTrue(ctl.ARDUINO_IP)                              # blieb erhalten (_connect setzt das Kennzeichen nicht mehr vor der Pruefung zurueck)


if __name__ == "__main__":
    unittest.main(verbosity=2)
