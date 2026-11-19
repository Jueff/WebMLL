# ----------------------------------------------------------------------------------------------
# Name:           web_settings_transfer.py
# Path:           _web/web_settings_transfer.py
# Version:        1.00
# Last Update:    2026-11-19
# Author:         Harold Linke
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-19  Neu (Issue 29): Einstellungen und Daten auf einen anderen PC uebernehmen. export_zip packt die Dateien des Anwenders
#                     aus dem Datenordner in eine ZIP, inspect_zip prueft sie, stage_import legt sie zur Uebernahme beim naechsten Start bereit,
#                     apply_pending uebernimmt sie dort VOR dem Laden der Konfiguration (sonst wuerde das Programm beim Beenden die alten
#                     Einstellungen wieder darueber schreiben). Passwort, Zugriff aus dem Netz, Protokolle und Zwischenspeicher gehoeren zum
#                     PC und sind nicht dabei; USB-Anschluss und Fensterlage der Konfiguration bleiben auf dem Zielrechner erhalten.
# ----------------------------------------------------------------------------------------------
"""Einstellungen sichern und auf einem anderen PC uebernehmen (Datei -> Einstellungen sichern / uebernehmen)."""
from __future__ import annotations

import io
import json
import logging
import os
import re
import shutil
import socket
import time
import zipfile

logger = logging.getLogger(__name__)

MANIFEST = "mll_settings.json"
FORMAT = "webMobaLedLib-Einstellungen"
PENDING_DIR = "settings_import_pending"
BACKUP_PREFIX = "settings_backup_"
MAX_TOTAL = 300 * 1024 * 1024          # Obergrenze fuer den entpackten Inhalt
KEEP_BACKUPS = 3                       # so viele Sicherungen vor einer Uebernahme bleiben erhalten

# Dateien im Datenordner, die zum Anwender (nicht zum PC) gehoeren
SETTING_FILES = ("MobaLedTest_param.json",      # Programm Einstellungen
                 "MobaLedTest_config.json",     # Farbtest, Palette, letzte Werte
                 "extensions.json",             # Liste der Erweiterungen
                 "esp32-ota.json")              # ESP32 OTA
SETTING_DIRS = ("extensions",)                  # geladene Erweiterungen
CONFIG_FILE = "MobaLedTest_config.json"
# Schluessel der Konfiguration, die zum PC gehoeren: bleiben auf dem Zielrechner, wie sie sind
LOCAL_KEYS = ("serportnumber", "serportname", "Z21Data", "pos_x", "pos_y", "win_height", "win_width")


def _table_files(data_dir: str, table_prefix: str) -> list:
    """Sicherungen der Tabellen im Datenordner: <Name der Zwischendatei>_<Arbeitsmappe>.json"""
    if not table_prefix:
        return []
    try:
        return sorted(f for f in os.listdir(data_dir)
                      if f.startswith(table_prefix + "_") and f.endswith(".json") and os.path.isfile(os.path.join(data_dir, f)))
    except OSError:
        return []


def _allowed(name: str, table_prefix: str, with_tables: bool) -> bool:
    if name == MANIFEST or name in SETTING_FILES:
        return True
    if any(name.startswith(d + "/") for d in SETTING_DIRS):
        return True
    if with_tables and table_prefix and "/" not in name and name.startswith(table_prefix + "_") and name.endswith(".json"):
        return True
    return False


def _safe_name(name: str) -> bool:
    return bool(name) and not name.startswith("/") and "\\" not in name and ".." not in name.split("/") and ":" not in name


def export_zip(data_dir: str, version: str, table_prefix: str = "", with_tables: bool = False) -> tuple[bytes, list]:
    """ZIP mit den Einstellungen. Rueckgabe: (Inhalt der ZIP, Liste der Dateien darin)."""
    files = []
    for name in SETTING_FILES:
        if os.path.isfile(os.path.join(data_dir, name)):
            files.append(name)
    for d in SETTING_DIRS:
        base = os.path.join(data_dir, d)
        for dp, _dn, fn in os.walk(base):
            for f in fn:
                files.append(os.path.relpath(os.path.join(dp, f), data_dir).replace("\\", "/"))
    tables = _table_files(data_dir, table_prefix) if with_tables else []
    files += tables
    manifest = {"format": FORMAT, "version": version, "date": time.strftime("%Y-%m-%d %H:%M:%S"), "computer": socket.gethostname(),
                "files": files, "tables": bool(tables), "table_prefix": table_prefix if tables else ""}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(MANIFEST, json.dumps(manifest, indent=1, ensure_ascii=False))
        for name in files:
            z.write(os.path.join(data_dir, name), name)
    return buf.getvalue(), files


def inspect_zip(data: bytes, table_prefix: str = "") -> dict:
    """Prueft die ZIP und gibt das Manifest zurueck (ValueError mit verstaendlicher Meldung, wenn sie nicht passt)."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as ex:
        raise ValueError("Das ist keine gültige ZIP-Datei.") from ex
    with z:
        names = z.namelist()
        if MANIFEST not in names:
            raise ValueError("Das ist keine Datei von „Einstellungen sichern“ (mll_settings.json fehlt).")
        try:
            manifest = json.loads(z.read(MANIFEST).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as ex:
            raise ValueError("Die Angaben in der ZIP-Datei sind nicht lesbar.") from ex
        if manifest.get("format") != FORMAT:
            raise ValueError("Das ist keine Datei von „Einstellungen sichern“.")
        total = 0
        for info in z.infolist():
            if info.is_dir():
                continue
            if not _safe_name(info.filename):
                raise ValueError("Die ZIP-Datei enthält einen unzulässigen Dateinamen: " + info.filename)
            if not _allowed(info.filename, manifest.get("table_prefix") or table_prefix, True):
                raise ValueError("Die ZIP-Datei enthält eine unerwartete Datei: " + info.filename)
            total += info.file_size
        if total > MAX_TOTAL:
            raise ValueError("Die ZIP-Datei ist zu groß.")
    manifest["count"] = len([n for n in names if not n.endswith("/") and n != MANIFEST])
    return manifest


def stage_import(data: bytes, data_dir: str, with_tables: bool) -> int:
    """Entpackt die ZIP in den Ordner der Uebernahme beim naechsten Start. Rueckgabe: Anzahl Dateien."""
    manifest = inspect_zip(data)
    pending = os.path.join(data_dir, PENDING_DIR)
    shutil.rmtree(pending, ignore_errors=True)
    os.makedirs(pending, exist_ok=True)
    count = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if name != MANIFEST and not _allowed(name, manifest.get("table_prefix", ""), with_tables):
                continue
            target = os.path.join(pending, name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            count += 1
    return count


def _merge_config(imported_path: str, local_path: str) -> None:
    """Konfiguration uebernehmen, die Schluessel des PCs (USB-Anschluss, Fensterlage) aber vom Zielrechner behalten."""
    try:
        with open(imported_path, "r", encoding="utf-8") as fh:
            new = json.load(fh)
    except (OSError, ValueError):
        return
    try:
        with open(local_path, "r", encoding="utf-8") as fh:
            old = json.load(fh)
    except (OSError, ValueError):
        old = {}
    if isinstance(new, dict) and isinstance(old, dict):
        for key in LOCAL_KEYS:
            if key in old:
                new[key] = old[key]
            else:
                new.pop(key, None)
        with open(imported_path, "w", encoding="utf-8") as fh:
            json.dump(new, fh, indent=2, ensure_ascii=False)


def apply_pending(data_dir: str) -> bool:
    """Beim Start VOR dem Laden der Konfiguration aufrufen: uebernimmt die bereitgelegten Dateien, sichert vorher die vorhandenen."""
    pending = os.path.join(data_dir, PENDING_DIR)
    if not os.path.isdir(pending):
        return False
    try:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(data_dir, BACKUP_PREFIX + stamp)
        names = []
        for dp, _dn, fn in os.walk(pending):
            for f in fn:
                rel = os.path.relpath(os.path.join(dp, f), pending).replace("\\", "/")
                if rel != MANIFEST:
                    names.append(rel)
        if os.path.isfile(os.path.join(pending, CONFIG_FILE)):
            _merge_config(os.path.join(pending, CONFIG_FILE), os.path.join(data_dir, CONFIG_FILE))
        for d in SETTING_DIRS:                       # Erweiterungen: der Ordner wird ersetzt, nicht gemischt
            if any(n.startswith(d + "/") for n in names) and os.path.isdir(os.path.join(data_dir, d)):
                os.makedirs(backup, exist_ok=True)
                shutil.move(os.path.join(data_dir, d), os.path.join(backup, d))
        for rel in names:
            target = os.path.join(data_dir, rel)
            if os.path.isfile(target):
                os.makedirs(os.path.dirname(os.path.join(backup, rel)), exist_ok=True)
                shutil.copy2(target, os.path.join(backup, rel))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(os.path.join(pending, rel), target)
        shutil.rmtree(pending, ignore_errors=True)
        logger.info("Einstellungen uebernommen (%d Dateien), Sicherung der alten: %s", len(names), backup)
        old = sorted(d for d in os.listdir(data_dir) if d.startswith(BACKUP_PREFIX))
        for d in old[:-KEEP_BACKUPS]:
            shutil.rmtree(os.path.join(data_dir, d), ignore_errors=True)
        return True
    except Exception:                                 # noqa: BLE001
        logger.exception("Einstellungen konnten nicht uebernommen werden")
        shutil.rmtree(pending, ignore_errors=True)
        return False
