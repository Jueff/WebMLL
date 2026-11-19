# Datei-Version: 1.03 (2026-11-19) - headless_extensions.py
# ----------------------------------------------------------------------------------------------
# Name:           headless_extensions.py
# Path:           headless/headless_extensions.py
# Version:        1.03
# Last Update:    2026-11-19
# Author:         Harold Linke
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-18  Neu: Liste der bekannten MobaLedLib Extensions (extensions_known.json), Haken aktiv/inaktiv (extensions.json im Datenordner),
#                     Laden einer Extension von GitHub in den Cache (Datenordner/extensions/<Id>)
#   1.02  2026-11-18  Eigene Extensions (Eingabe: Name, Name@=Version, Name=Adresse oder nur Adresse; parse_spec, add_custom, remove_custom, all_entries), Hinweis-Merker, find_disabled_used (Rueckfrage beim Oeffnen einer Datei)
#   1.03  2026-11-19  library_info: Name und Beschreibung aus libraries.json (oder library.json) der Extension fuer die Anzeige (Wunsch Juergen, Issue 6)
#   1.01  2026-11-18  load_properties: toleranter Leser fuer MobaLedLib.properties (Schluessel ohne Anfuehrungszeichen, fehlende Kommas, Kommas vor ] oder }, Kommentare), wie der Leser im Excel-Programm
# ----------------------------------------------------------------------------------------------
"""MobaLedLib Extensions (MLX) ohne Oberflaeche.

Bekannte Extensions stehen in extensions_known.json (Paket). Gruppe "standard" ist vorab aktiv, "optional" vorab aus. Der Anwender setzt nur den Haken
(extensions.json im Datenordner). Eine Extension, die im Paket liegt (Ordner libraries), braucht keinen Download; die anderen werden beim Aktivieren
von ihrer GitHub-Adresse als ZIP geladen und im Datenordner (extensions/<Id>) abgelegt. Beide Orte enthalten die Datei MobaLedLib.properties,
die M38_Extensions liest. Extensions, die nicht in der Liste stehen (zum Beispiel von Hand in den Ordner libraries gelegt), bleiben wie bisher immer aktiv."""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import re
import tempfile
import urllib.request
import zipfile

import userdata

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWN_FILE = os.path.join(ROOT, "extensions_known.json")
LIB_DIR = os.path.join(ROOT, "libraries")
PROPS = "MobaLedLib.properties"
MAX_BYTES = 30 * 1048576


class ExtensionError(Exception):
    pass


def known() -> list:
    """Die bekannten Extensions (Liste von Eintraegen mit id, name, url, group, bundled, description, hardware)"""
    try:
        with open(KNOWN_FILE, "r", encoding="utf-8") as fh:
            return list(json.load(fh).get("extensions", []))
    except (OSError, ValueError, AttributeError):
        logger.warning("extensions_known.json nicht lesbar: %s", KNOWN_FILE)
        return []


def _settings_file() -> str:
    return userdata.path("extensions.json")


def _read() -> dict:  # v1.02
    try:
        with open(_settings_file(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(data: dict) -> None:  # v1.02
    tmp = _settings_file() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, _settings_file())


def _load_flags() -> dict:
    data = _read().get("enabled", {})
    return {str(k): bool(v) for k, v in data.items()} if isinstance(data, dict) else {}


def custom() -> list:  # v1.02
    """Eigene Extensions als Eintraege wie known(): id = Ordnername, group = custom"""
    out = []
    for c in _read().get("custom", []):
        try:
            out.append({"id": c["folder"], "name": c.get("label") or c["folder"], "url": c.get("url", ""), "ref": c.get("ref", ""), "kind": c.get("kind", "url"),
                        "spec": c.get("spec", ""), "version": c.get("version", ""), "group": "custom", "bundled": False,
                        "description": "Id: " + str(c.get("props_id", "")), "hardware": "", "props_id": c.get("props_id", "")})
        except (KeyError, TypeError):
            continue
    return out


def all_entries() -> list:  # v1.02
    return known() + custom()


def entry(ext_id: str):  # v1.02
    return next((e for e in all_entries() if e.get("id") == ext_id), None)


def is_enabled(ext_id: str) -> bool:
    """Ist die Extension eingeschaltet? Unbekannte (nicht in der Liste) sind immer eingeschaltet. Eigene sind vorab eingeschaltet."""
    e = entry(ext_id)
    if e is None:
        return True
    flags = _load_flags()
    if ext_id in flags:
        return flags[ext_id]
    return e.get("group") in ("standard", "custom")


def set_enabled(ext_id: str, value: bool) -> None:
    data = _read()
    flags = _load_flags()
    flags[ext_id] = bool(value)
    data["enabled"] = flags
    _write(data)


def warned() -> bool:  # v1.02: Hinweis auf fremden Code wurde schon einmal bestaetigt
    return bool(_read().get("warned"))


def set_warned() -> None:  # v1.02
    data = _read()
    data["warned"] = True
    _write(data)


def cache_dir() -> str:
    return userdata.path("extensions")


def local_dir(e: dict):
    """Ordner der Extension (im Paket oder im Cache), in dem MobaLedLib.properties liegt, sonst None"""
    for base in (LIB_DIR, cache_dir()):
        path = os.path.join(base, e["id"])
        if os.path.isfile(os.path.join(path, PROPS)):
            return path
    return None


def library_info(e: dict) -> dict:  # v1.03
    """Name und Beschreibung aus libraries.json (oder library.json) im Ordner der Extension: {'name': ..., 'description': ...}; fehlt etwas, fehlt der Schluessel"""
    path = local_dir(e)
    if not path:
        return {}
    for fname in ("libraries.json", "library.json"):
        fp = os.path.join(path, fname)
        if not os.path.isfile(fp):
            continue
        try:
            with open(fp, encoding="utf-8-sig") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(data, list):
            data = next((d for d in data if isinstance(d, dict)), {})
        if isinstance(data, dict):
            return {k: str(data[k]).strip() for k in ("name", "description") if isinstance(data.get(k), str) and data[k].strip()}
    return {}


def status(e: dict) -> str:
    """'bundled' (im Paket), 'loaded' (im Cache) oder 'missing'"""
    path = local_dir(e)
    if path is None:
        return "missing"
    return "bundled" if os.path.dirname(path) == LIB_DIR else "loaded"


def cached_properties() -> list:
    """Pfade der MobaLedLib.properties aller eingeschalteten Extensions im Cache (zusaetzlich zu libraries)"""
    out = []
    for e in known() + custom():
        if e.get("bundled"):
            continue
        path = os.path.join(cache_dir(), e["id"], PROPS)
        if os.path.isfile(path) and is_enabled(e["id"]):
            out.append(path)
    return out


def zip_url(e: dict) -> str:
    url = str(e.get("url", "")).strip()
    m = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", url)
    if m:
        return "https://github.com/%s/%s/archive/%s.zip" % (m.group(1), m.group(2), e.get("ref") or "HEAD")
    if url.startswith("https://") and url.lower().split("?")[0].endswith(".zip"):
        return url
    raise ExtensionError("Nur GitHub-Adressen (https://github.com/Besitzer/Name) oder Adressen einer ZIP-Datei sind erlaubt: " + url)


def _store(e: dict, src: str) -> str:  # v1.02
    """Den Ordner mit MobaLedLib.properties unterhalb von src in den Cache verschieben"""
    found = None
    for root, _dirs, files in os.walk(src):
        if PROPS in files:
            found = root
            break
    if found is None:
        raise ExtensionError(PROPS + " fehlt: keine MobaLedLib Extension.")
    dest = os.path.join(cache_dir(), e["id"])
    os.makedirs(cache_dir(), exist_ok=True)
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)
    shutil.move(found, dest)
    return dest


def _registry_install(e: dict, dest: str) -> None:  # v1.02
    """Paket aus der PlatformIO-Registry in den Ordner dest laden (pio pkg install)"""
    pio = shutil.which("pio") or shutil.which("platformio")
    if not pio:
        try:
            import proggen.M08_ARDUINO as M08
            pio = M08.Find_PIO()
        except Exception:                                # noqa: BLE001
            pio = ""
    if not pio:
        raise ExtensionError("PlatformIO wurde nicht gefunden.")
    spec = e["name"] + (("@=" + e["version"]) if e.get("version") else "")
    try:
        res = subprocess.run([pio, "pkg", "install", "--global", "--storage-dir", dest, "--library", spec, "--skip-dependencies"],
                             capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as ex:
        raise ExtensionError(str(ex)) from ex
    if res.returncode != 0:
        raise ExtensionError(((res.stderr or res.stdout) or "pio pkg install ist fehlgeschlagen").strip()[-300:])


def download(e: dict, progress=None, timeout: float = 30.0) -> str:
    """Extension laden und im Cache ablegen. Rueckgabe: Ordner. ExtensionError bei Fehlern (Netz, kein MobaLedLib.properties)."""
    tmp = tempfile.mkdtemp(prefix="mll_ext_")
    try:
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        if e.get("kind") == "registry":  # v1.02
            _registry_install(e, src)  # v1.02
            return _store(e, src)  # v1.02
        zpath = os.path.join(tmp, "ext.zip")
        request = urllib.request.Request(zip_url(e), headers={"User-Agent": "webmobaledlib-extensions"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp, open(zpath, "wb") as out:
                total = int(resp.headers.get("Content-Length") or 0)
                done = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    done += len(chunk)
                    if done > MAX_BYTES:
                        raise ExtensionError("Die Datei ist ungewoehnlich gross: Abbruch.")
                    out.write(chunk)
                    if progress:
                        progress(done, total)
        except ExtensionError:
            raise
        except Exception as ex:                          # noqa: BLE001  (Netz, DNS, HTTP-Fehler)
            raise ExtensionError(str(ex)) from ex
        if not zipfile.is_zipfile(zpath):
            raise ExtensionError("Die geladene Datei ist kein ZIP.")
        with zipfile.ZipFile(zpath) as zf:
            for name in zf.namelist():
                target = os.path.normpath(os.path.join(src, name))
                if os.path.commonpath([src, target]) != src:
                    raise ExtensionError("Unzulaessiger Pfad im ZIP: " + name)
            zf.extractall(src)
        return _store(e, src)  # v1.02
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def load_properties(path: str):  # v1.01
    """MobaLedLib.properties lesen. Die Dateien der Extensions sind oft kein strenges JSON (der Leser im Excel-Programm nahm sie an):
    Schluessel ohne Anfuehrungszeichen, fehlende Kommas zwischen Eintraegen, ueberzaehlige Kommas, Kommentare. Rueckgabe: dict, bei Fehler None."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except ValueError:
        pass
    # Zeichenkette fuer Zeichenkette bearbeiten, damit Inhalte in Anfuehrungszeichen unveraendert bleiben
    parts = re.split(r'("(?:[^"\\\n]|\\.)*")', text)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            part = re.sub(r"//[^\n]*", "", part)                                   # Kommentare bis Zeilenende
            part = re.sub(r"/\*.*?\*/", "", part, flags=re.S)
            part = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)", r'\1"\2"\3', part)   # Schluessel ohne Anfuehrungszeichen
        out.append(part)
    text = "".join(out)
    # Komma zwischen zwei Eintraegen ergaenzen: Wert (Zeichenkette, Zahl, ], }) gefolgt von einem Schluessel in der naechsten Zeile
    text = re.sub(r'("|\d|\]|\}|true|false|null)(\s*\n\s*)(")(?=[^"\n]*"\s*:)', r"\1,\2\3", text)
    text = re.sub(r",(\s*[\]}])", r"\1", text)                                    # Komma vor ] oder }
    try:
        data = json.loads(text)
    except ValueError as ex:
        logger.warning("MobaLedLib.properties nicht lesbar (%s): %s", path, ex)
        return None
    return data if isinstance(data, dict) else None


# ------------------------------------------------------------------ Eigene Extensions  # v1.02
_NAME = r"[A-Za-z0-9_.-]+"


def parse_spec(line: str) -> dict:
    """Eine Zeile der eigenen Liste auswerten. Erlaubt:
         Name                    Paket aus der PlatformIO-Registry, aktuelle Version
         Name@=1.1.0             genau diese Version (auch Name@1.1.0)
         Name=https://github.com/Besitzer/Repo     Code aus dem Repository (nach # ein Tag oder Zweig)
         https://github.com/Besitzer/Repo          wie oben, der Name ist der Name des Repositorys
       Rueckgabe: dict mit kind (url oder registry), name, url, ref, version, folder, spec. ExtensionError bei Fehlern."""
    spec = (line or "").strip()
    if not spec or any(c.isspace() for c in spec) or any(c in spec for c in '"\'`;|&<>'):
        raise ExtensionError("Ungueltige Eingabe: keine Leerzeichen und keine Sonderzeichen.")
    if spec.startswith("https://") or "=https://" in spec:
        name, url = ("", spec) if spec.startswith("https://") else spec.split("=", 1)
        if name and not re.fullmatch(_NAME, name):
            raise ExtensionError("Ungueltiger Name: " + name)
        url, _, ref = url.partition("#")
        entry_ = {"kind": "url", "name": name, "url": url, "ref": ref, "version": "", "spec": spec}
        zip_url(entry_)                                              # prueft die Adresse
        if not name:
            tail = url.rstrip("/").split("?")[0].split("/")[-1]
            name = re.sub(r"\.(git|zip)$", "", tail)
        entry_["name"] = name
    else:
        m = re.fullmatch(r"(%s)(?:@=?([A-Za-z0-9_.+*^~-]+))?" % _NAME, spec)
        if not m:
            raise ExtensionError("Ungueltige Eingabe: erwartet Name, Name@=Version, Name=https://… oder https://…")
        entry_ = {"kind": "registry", "name": m.group(1), "url": "", "ref": "", "version": m.group(2) or "", "spec": spec}
    folder = re.sub(r"[^A-Za-z0-9_.-]", "_", entry_["name"]).strip(".") or "Extension"
    entry_["folder"] = folder
    entry_["id"] = folder
    return entry_


def add_custom(spec: str, progress=None) -> dict:
    """Eigene Extension hinzufuegen: Eingabe pruefen, laden, MobaLedLib.properties lesen, speichern, einschalten. Rueckgabe: der Eintrag."""
    e = parse_spec(spec)
    if entry(e["id"]) is not None:
        raise ExtensionError("Es gibt schon eine Erweiterung mit dem Namen " + e["id"])
    if os.path.isdir(os.path.join(LIB_DIR, e["id"])):
        raise ExtensionError("Im Ordner libraries liegt schon eine Erweiterung mit dem Namen " + e["id"])
    dest = download(e, progress)
    props = load_properties(os.path.join(dest, PROPS))
    if not props or not props.get("id"):
        shutil.rmtree(dest, ignore_errors=True)
        raise ExtensionError(PROPS + " ist nicht lesbar oder enthaelt keine id.")
    data = _read()
    lst = list(data.get("custom", []))
    lst.append({"spec": e["spec"], "folder": e["folder"], "kind": e["kind"], "url": e["url"], "ref": e["ref"], "version": e["version"],
                "label": e["folder"], "props_id": props["id"]})
    data["custom"] = lst
    flags = _load_flags()
    flags[e["id"]] = True
    data["enabled"] = flags
    _write(data)
    return entry(e["id"])


def remove_custom(ext_id: str) -> None:
    """Eigene Extension entfernen (Eintrag, Haken und Cache-Ordner)"""
    data = _read()
    data["custom"] = [c for c in data.get("custom", []) if c.get("folder") != ext_id]
    flags = _load_flags()
    flags.pop(ext_id, None)
    data["enabled"] = flags
    _write(data)
    shutil.rmtree(os.path.join(cache_dir(), ext_id), ignore_errors=True)


def type_names(e: dict) -> list:
    """Namen der Konstruktoren (TypeName) einer Extension: aus der Datei, sonst aus der Liste (types)"""
    path = local_dir(e)
    if path:
        props = load_properties(os.path.join(path, PROPS))
        if props:
            return [t.get("TypeName") for t in props.get("types", []) if isinstance(t, dict) and t.get("TypeName")]
    return list(e.get("types", []))


def find_disabled_used(texts) -> list:
    """Welche ausgeschalteten Extensions werden in den Zellentexten benutzt (EX.<TypeName>( ...)? Rueckgabe: Eintraege"""
    used = [t for t in texts if isinstance(t, str) and "EX." in t]
    if not used:
        return []
    out = []
    for e in all_entries():
        if is_enabled(e["id"]):
            continue
        names = type_names(e)
        if any(("EX." + n + "(") in t for n in names for t in used):
            out.append(e)
    return out
