#!/usr/bin/env bash
# Datei-Version: 1.11 (2026-11-24) - install_linux.sh, gilt fuer webMobaLedLib 3.47
# 1.11: Symbol heisst MobaLedLib Studio; Symbole mit den frueheren Namen werden entfernt
# 1.10: Anzeigename MobaLedLib Studio in den Meldungen (Name des Symbols unveraendert)
# Installiert die Web-Oberflaeche von webMobaLedLib auf einem Linux-Desktop (Debian, Ubuntu, Linux Mint, Fedora, Arch ...):
# im eigenen Benutzerkonto, ohne Systemdienst. Es entsteht eine Python-Umgebung im Projektordner (venv_web), ein Starter im
# Anwendungsmenue und ein Symbol auf dem Schreibtisch. (Raspberry Pi als Dienst: pi/install_pi.sh)
#
# Aufruf im Ordner install (als normaler Benutzer, nicht mit sudo):
#     bash install_linux.sh [Optionen]
#   --with-arduino-ide    ARDUINO IDE 1.8.19 nach ~/arduino-1.8.19 laden (ohne root)
#   --with-arduino-libs   Bibliothek MobaLedLib samt FastLED in der geforderten Version installieren (braucht die IDE)
#   --with-platformio     PlatformIO (Ersatz fuer die ARDUINO IDE) in eine eigene Python-Umgebung ~/.platformio/penv installieren (install_platformio.sh); seit 1.07 der STANDARD
#   --no-platformio       PlatformIO NICHT installieren (zum Beispiel wer nur die ARDUINO IDE benutzt)
#   --no-desktop-icon     kein Symbol auf dem Schreibtisch (der Eintrag im Anwendungsmenue bleibt)
#   --no-dialout          die Gruppe dialout (USB-Anschluss des Arduino) nicht eintragen
#   --no-check            den Test der Installation (pi_check.py) ueberspringen
#   --server              (seit 1.09) Server ohne Bildschirm: Zugriff aus dem Netz mit Passwort, als Systemdienst (mobaledlib-web, startet beim Booten); kein Symbol, kein Menueeintrag
#   --password PW         (mit --server) Passwort fuer den Zugriff aus dem Netz; ohne die Option fragt das Skript (zweimal, mindestens 4 Zeichen). Auch: Umgebungsvariable MLL_SERVER_PASSWORD
#   --port N              (mit --server) Port der Web-Oberflaeche (Voreinstellung 8080)
#   --no-service          (mit --server) keinen Systemdienst einrichten, nur Passwort und Zugriff aus dem Netz vorbereiten
set -uo pipefail

WITH_IDE=0; WITH_LIBS=0; WITH_PIO=1; DESKTOP_ICON=1; DIALOUT=1; RUN_CHECK=1
SERVER=0; SERVER_OPTS=0; SERVICE=1; SERVER_PORT=8080; SERVER_PW="${MLL_SERVER_PASSWORD:-}"   # v1.09
while [ $# -gt 0 ]; do   # v1.09 (vorher for a in "$@")
  a="$1"; shift   # v1.09
  case "$a" in
    --with-arduino-ide)  WITH_IDE=1; WITH_LIBS=1 ;;
    --with-arduino-libs) WITH_LIBS=1 ;;
    --with-platformio)   WITH_PIO=1 ;;
    --no-platformio)     WITH_PIO=0 ;;
    --no-desktop-icon)   DESKTOP_ICON=0 ;;
    --no-dialout)        DIALOUT=0 ;;
    --no-check)          RUN_CHECK=0 ;;
    --server)            SERVER=1; DESKTOP_ICON=0 ;;   # v1.09
    --no-service)        SERVICE=0; SERVER_OPTS=1 ;;   # v1.09
    --password)          [ $# -ge 1 ] || { echo "--password braucht einen Wert."; exit 1; }; SERVER_PW="$1"; SERVER_OPTS=1; shift ;;   # v1.09
    --port)              [ $# -ge 1 ] || { echo "--port braucht einen Wert."; exit 1; }; SERVER_PORT="$1"; SERVER_OPTS=1; shift ;;   # v1.09
    -h|--help)           sed -n '3,20p' "$0"; exit 0 ;;   # v1.09: Zeilen 3 bis 21
    *) echo "Unbekannte Option: $a"; exit 1 ;;
  esac
done

case "$SERVER_PORT" in ''|*[!0-9]*) echo "Ungueltiger Port: $SERVER_PORT"; exit 1 ;; esac   # v1.09
if [ "$SERVER" != "1" ] && [ "$SERVER_OPTS" = "1" ]; then echo "Die Optionen --password, --port und --no-service gelten nur mit --server."; exit 1; fi   # v1.09
cd "$(dirname "$0")" || exit 1
HERE="$(pwd)"
APPDIR="$(cd .. && pwd)"
VENV="$APPDIR/venv_web"
[ "$(uname)" = "Linux" ] || { echo "Dieses Skript ist fuer Linux (macOS: install_mac.command)."; exit 1; }
if [ "$(id -u)" -eq 0 ] && [ "${MLL_ALLOW_ROOT:-0}" != "1" ]; then
  echo "Bitte als normaler Benutzer starten (ohne sudo): die Dateien gehoeren sonst root."; exit 1
fi
[ -f "$APPDIR/webmobaledlib.py" ] || { echo "FEHLER: webmobaledlib.py nicht gefunden in $APPDIR (der Ordner install gehoert neben webmobaledlib.py)."; exit 1; }
fail() { echo; echo "Die Installation wurde nicht abgeschlossen."; exit 1; }

echo
echo "============================================================"
echo " MobaLedLib Studio - Installation der Web-Oberflaeche (Linux)"
echo "============================================================"
. /etc/os-release 2>/dev/null || true
echo " System:        ${PRETTY_NAME:-unbekannt} ($(uname -m))"
case "$(uname -m)" in
  x86_64|aarch64|arm64) ;;
  *) echo " ACHTUNG: Auf 32-Bit-Systemen und anderen Prozessorarten gibt es fuer einige Python-Pakete keine fertigen Dateien; die Installation kann scheitern." ;;
esac
echo " Projektordner: $APPDIR"
echo

# --- 1. Systempakete (Python mit venv und pip, curl und xz fuer den Download der IDE, git: PlatformIO holt die Plattform des Raspberry Pi Pico aus GitHub)
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
install_packages() {
  if command -v apt-get >/dev/null 2>&1; then                      # Debian, Ubuntu, Linux Mint
    local missing=() p
    # v1.09: die Liste steht jetzt in $want (vorher feste Liste python3 python3-venv python3-pip curl xz-utils git)
    local want="python3 python3-venv python3-pip curl xz-utils git"; [ "$SERVER" = "1" ] && want="$want xvfb"   # v1.09: xvfb fuer die ARDUINO IDE auf dem Server
    for p in $want; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
    if [ ${#missing[@]} -gt 0 ]; then
      echo "Systempakete installieren (sudo-Passwort wird abgefragt): ${missing[*]}"
      $SUDO apt-get update && $SUDO apt-get install -y "${missing[@]}" || return 1
    fi
  elif command -v dnf >/dev/null 2>&1; then                         # Fedora
    $SUDO dnf install -y python3 python3-pip curl xz git || return 1
  elif command -v pacman >/dev/null 2>&1; then                      # Arch, Manjaro
    $SUDO pacman -S --needed --noconfirm python python-pip curl xz git || return 1
  elif command -v zypper >/dev/null 2>&1; then                      # openSUSE
    $SUDO zypper install -y python3 python3-pip curl xz git || return 1
  else
    echo "Paketverwaltung nicht erkannt: bitte Python 3.10+, venv, pip, curl und xz selbst installieren."
  fi
  return 0
}
if [ "${MLL_SKIP_PACKAGES:-0}" != "1" ]; then install_packages || fail; fi

# --- 2. Python 3.10 oder neuer
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then PY="$(command -v "$c")"; break; fi
done
if [ -z "$PY" ]; then
  echo "Python 3.10 oder neuer wurde nicht gefunden (gebraucht: Linux Mint 21 / Ubuntu 22.04 / Debian 12 oder neuer)."
  echo "Auf aelteren Systemen Python nachinstallieren (zum Beispiel ueber deadsnakes oder pyenv) und das Skript noch einmal starten."
  fail
fi
echo "Python: $PY ($("$PY" --version 2>&1))"

# --- 3. Python-Umgebung und Pakete
echo; echo "[1/5] Python-Umgebung anlegen: $VENV"
if [ ! -x "$VENV/bin/python" ]; then
  "$PY" -m venv "$VENV" || { echo "venv fehlgeschlagen. Debian/Ubuntu/Mint: sudo apt install python3-venv"; fail; }
fi
echo "[2/5] Pakete installieren (das dauert einige Minuten) ..."
if [ "${MLL_SKIP_PIP:-0}" != "1" ]; then
  "$VENV/bin/python" -m pip install --upgrade pip || fail
  if ! "$VENV/bin/python" -m pip install --prefer-binary -r "$HERE/requirements-web.txt"; then
    echo
    echo "FEHLER beim Installieren der Python-Pakete (siehe oben, zum Beispiel \"Failed to build <Paket>\")."
    echo "Diagnose, bitte mitschicken: Prozessor $(uname -m), $("$VENV/bin/python" --version 2>&1) ($(getconf LONG_BIT 2>/dev/null) Bit), pip $("$VENV/bin/python" -m pip --version 2>&1 | cut -d' ' -f2), $(ldd --version 2>&1 | head -1)"
    echo "Ursachen: kein Internet, 32-Bit-System, Python zu alt oder zu neu fuer ein Paket (dann fehlen fertige Dateien und pip versucht, es zu uebersetzen)."
    fail
  fi
fi

# --- 4. USB-Anschluss: Gruppe dialout
echo "[3/5] Zugriff auf die seriellen Anschluesse (Arduino, Pico)"
if [ "$DIALOUT" = "1" ] && ! id -nG "$USER" 2>/dev/null | tr ' ' '\n' | grep -qx dialout; then
  if getent group dialout >/dev/null 2>&1; then
    echo "Benutzer $USER wird in die Gruppe dialout aufgenommen (sudo-Passwort)."
    $SUDO usermod -aG dialout "$USER" && echo "-> Bitte einmal ab- und wieder anmelden, damit es wirkt."
  fi
else
  echo "Gruppe dialout: in Ordnung (oder uebersprungen)."
fi

# --- 5. ARDUINO IDE und Bibliotheken (optional)
echo "[4/5] ARDUINO IDE"
IDE_DIR="$HOME/arduino-1.8.19"
install_ide() {
  case "$(uname -m)" in
    x86_64)          v=linux64 ;;
    aarch64|arm64)   v=linuxaarch64 ;;
    armv7l|armv6l)   v=linuxarm ;;
    i?86)            v=linux32 ;;
    *) echo "Unbekannte Architektur $(uname -m): IDE von Hand installieren."; return 1 ;;
  esac
  [ -x "$IDE_DIR/arduino" ] && { echo "Schon vorhanden: $IDE_DIR/arduino"; return 0; }
  local tmp; tmp="$(mktemp -d)"
  echo "Lade https://downloads.arduino.cc/arduino-1.8.19-$v.tar.xz (etwa 150 MB) ..."
  if curl -fL --retry 3 -o "$tmp/ide.tar.xz" "https://downloads.arduino.cc/arduino-1.8.19-$v.tar.xz" && tar -xf "$tmp/ide.tar.xz" -C "$HOME"; then
    echo "Installiert: $IDE_DIR/arduino"; rm -rf "$tmp"; return 0
  fi
  rm -rf "$tmp"; echo "Download oder Auspacken fehlgeschlagen."; return 1
}
if [ "$WITH_IDE" = "1" ]; then install_ide || echo "(die IDE bitte von Hand installieren)"; fi
IDE_EXE=""
for c in "${MLL_ARDUINO_EXE:-}" "$IDE_DIR/arduino" /opt/arduino-1.8*/arduino "$HOME"/arduino-1.8*/arduino "$(command -v arduino 2>/dev/null || true)"; do
  [ -n "$c" ] && [ -x "$c" ] && { IDE_EXE="$c"; break; }
done
if [ -n "$IDE_EXE" ]; then
  echo "ARDUINO IDE gefunden: $IDE_EXE"
  if [ "$WITH_LIBS" = "1" ] && [ -f "$APPDIR/pi/install_arduino_libs.sh" ]; then
    echo "Bibliothek MobaLedLib installieren (dauert einige Minuten) ..."
    MLL_ARDUINO_EXE="$IDE_EXE" bash "$APPDIR/pi/install_arduino_libs.sh" || echo "(Bibliotheken: siehe Meldungen oben; Nachholen: Optionen, Update, Status der Bibliotheken; siehe Anleitung 2.3)"
  fi
# elif-Zweig statt else (v1.08): Mit PlatformIO (Standard) wird die ARDUINO IDE nicht gebraucht, dann keine Meldung
elif [ "$WITH_PIO" != "1" ]; then
  echo "Keine ARDUINO IDE gefunden. Installieren mit:  bash install_linux.sh --with-arduino-ide   (oder PlatformIO: bash install_linux.sh --with-platformio)"
fi

# --- 5b. PlatformIO (Standard, ausser mit --no-platformio)
if [ "$WITH_PIO" = "1" ]; then
  MLL_PYTHON="$PY" bash "$HERE/install_platformio.sh" || echo "(PlatformIO: siehe Meldungen oben; Nachholen: bash install_platformio.sh)"
fi

# --- 6. Starter, Symbol und Eintraege (nicht auf dem Server)
if [ "$SERVER" = "1" ]; then   # v1.09
  echo "[5/5] Server: Zugriff aus dem Netz mit Passwort"
  set_server_password() {
    local pw="$SERVER_PW" pw2 tries=0 err
    while :; do
      if [ -z "$pw" ]; then
        if [ ! -t 0 ]; then echo "Kein Passwort angegeben und keine Eingabe moeglich: bitte --password PW oder MLL_SERVER_PASSWORD verwenden."; return 1; fi
        read -r -s -p "Passwort fuer den Zugriff aus dem Netz (mindestens 4 Zeichen): " pw; echo
        read -r -s -p "Passwort wiederholen: " pw2; echo
        [ "$pw" = "$pw2" ] || { echo "Die beiden Eingaben sind nicht gleich."; pw=""; tries=$((tries+1)); [ $tries -ge 3 ] && return 1; continue; }
      fi
      err="$(cd "$APPDIR" && MLL_HEADLESS=1 MLL_TK_ROOT=0 MLL_NEWPW="$pw" "$VENV/bin/python" - <<'PY' 2>&1
import os, sys
sys.path.insert(0, os.getcwd())
from _web import web_password as w
pw = os.environ["MLL_NEWPW"]
e = w.validate_new(pw, pw)
if e:
    print(e)
    sys.exit(2)
w.set_password(pw)
PY
)" && { echo "Passwort gesetzt (nur verschluesselt gespeichert, Benutzername: mobaledlib)."; return 0; }
      echo "$err"; pw=""; tries=$((tries+1))
      [ -n "$SERVER_PW" ] && return 1          # per Aufruf angegeben: nicht erneut fragen
      [ $tries -ge 3 ] && return 1
    done
  }
  set_server_password || fail
  if [ "$SERVICE" = "1" ]; then
    if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
      echo "Systemdienst mobaledlib-web einrichten (sudo-Passwort wird abgefragt) ..."
      XVFB=""; command -v xvfb-run >/dev/null 2>&1 && XVFB="$(command -v xvfb-run) -a -s \"-screen 0 1280x1024x24\" "
      ENVF="$(mktemp)"; UNIT="$(mktemp)"
      printf 'MLL_HOST=0.0.0.0\nMLL_PORT=%s\nMLL_USER=mobaledlib\n' "$SERVER_PORT" > "$ENVF"
      {
        echo "# Datei-Version: 1.00 (2026-11-15) - mobaledlib-web.service (erzeugt von install_linux.sh --server)"
        echo "[Unit]"; echo "Description=MobaLedLib Studio Programmgenerator (Web-Oberflaeche, Server)"
        echo "After=network-online.target"; echo "Wants=network-online.target"; echo
        echo "[Service]"; echo "Type=simple"; echo "User=$(id -un)"; echo "Group=$(id -gn)"
        echo "SupplementaryGroups=dialout"; echo "WorkingDirectory=$APPDIR"
        echo "EnvironmentFile=-/etc/mobaledlib-web.env"
        echo "Environment=MLL_HEADLESS=1"; echo "Environment=MLL_TK_ROOT=0"; echo "Environment=MLL_NO_BROWSER=1"; echo "Environment=PYTHONUNBUFFERED=1"
        echo "ExecStart=${XVFB}$VENV/bin/python $APPDIR/webmobaledlib.py"
        echo "Restart=always"; echo "RestartSec=3"; echo
        echo "[Install]"; echo "WantedBy=multi-user.target"
      } > "$UNIT"
      if $SUDO install -m 644 "$ENVF" /etc/mobaledlib-web.env && $SUDO install -m 644 "$UNIT" /etc/systemd/system/mobaledlib-web.service \
         && $SUDO systemctl daemon-reload && $SUDO systemctl enable mobaledlib-web && $SUDO systemctl restart mobaledlib-web; then
        echo "Dienst mobaledlib-web laeuft und startet beim Booten (Status: systemctl status mobaledlib-web)."
        SERVICE_OK=1
      else
        echo "Der Systemdienst konnte nicht eingerichtet werden (siehe Meldungen oben)."
      fi
      rm -f "$ENVF" "$UNIT"
    else
      echo "Kein systemd gefunden: der Dienst wird nicht eingerichtet. Starten von Hand:"
      echo "  MLL_HOST=0.0.0.0 MLL_PORT=$SERVER_PORT MLL_HEADLESS=1 MLL_NO_BROWSER=1 $VENV/bin/python $APPDIR/webmobaledlib.py"
    fi
  else
    echo "Ohne Dienst (--no-service): Starten mit  MLL_HOST=0.0.0.0 MLL_PORT=$SERVER_PORT MLL_HEADLESS=1 MLL_NO_BROWSER=1 $VENV/bin/python $APPDIR/webmobaledlib.py"
  fi
else   # v1.09: ab hier Starter und Symbol nur fuer Desktop-Installationen
echo "[5/5] Starter und Symbol"
chmod +x "$HERE/start_linux.sh" 2>/dev/null
[ -f "$HERE/mobaledlib.png" ] || "$VENV/bin/python" "$HERE/make_icons.py" "$HERE" || echo "(Symbol nicht erzeugt)"
make_entry() {
  printf '[Desktop Entry]\nType=Application\nName=MobaLedLib Studio\nGenericName=Programmgenerator Modellbahnbeleuchtung\n'
  printf 'Comment=MobaLedLib Studio Programmgenerator starten (Web-Oberflaeche)\nExec="%s/start_linux.sh"\nIcon=%s/mobaledlib.png\n' "$HERE" "$HERE"
  printf 'Terminal=false\nCategories=Development;Electronics;\nStartupNotify=false\n'
}
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APPS"
rm -f "$APPS/pyMobaLedLib.desktop" "$APPS/webMobaLedLib.desktop"          # Eintraege unter den frueheren Namen entfernen
make_entry > "$APPS/MobaLedLibStudio.desktop"; chmod +x "$APPS/MobaLedLibStudio.desktop"
echo "Eintrag im Anwendungsmenue: $APPS/MobaLedLibStudio.desktop"
if [ "$DESKTOP_ICON" = "1" ]; then
  DESK="$(xdg-user-dir DESKTOP 2>/dev/null || true)"; [ -z "$DESK" ] || [ "$DESK" = "$HOME" ] && DESK="$HOME/Desktop"
  if [ -d "$DESK" ]; then
    rm -f "$DESK/pyMobaLedLib.desktop" "$DESK/webMobaLedLib.desktop"        # Symbole unter den frueheren Namen entfernen
    make_entry > "$DESK/MobaLedLibStudio.desktop"; chmod +x "$DESK/MobaLedLibStudio.desktop"
    gio set "$DESK/MobaLedLibStudio.desktop" metadata::trusted true >/dev/null 2>&1 || true    # Cinnamon/GNOME: Starter vertrauen
    echo "Symbol auf dem Schreibtisch: $DESK/MobaLedLibStudio.desktop"
  else
    echo "Kein Schreibtisch-Ordner gefunden ($DESK): nur der Eintrag im Anwendungsmenue."
  fi
fi
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true
fi   # v1.09: Ende nur Desktop

# --- Test der Installation
if [ "$RUN_CHECK" = "1" ]; then
  echo; echo "Test der Installation (dauert etwa eine Minute) ..."
  MLL_TK_ROOT=0 MLL_HEADLESS=1 "$VENV/bin/python" "$APPDIR/pi_check.py" || echo "Der Test meldet Probleme, siehe die Meldungen oben."
fi

if [ "$SERVER" = "1" ]; then   # v1.09
  IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  echo
  echo "============================================================"
  echo " Fertig (Server). Oberflaeche:  http://${IP:-<IP-des-Servers>}:$SERVER_PORT"
  echo "                  Benutzer: mobaledlib   Passwort: das eben gesetzte"
  echo " Das Passwort aendern: Programm Einstellungen, Zugriff ueber das Netz."
  echo " ACHTUNG: Nur im Heimnetz betreiben, nie ungeschuetzt aus dem Internet erreichbar machen."
  echo " Firewall: Der Port $SERVER_PORT muss im Heimnetz erreichbar sein (zum Beispiel: sudo ufw allow from 192.168.0.0/16 to any port $SERVER_PORT proto tcp)."
  echo "============================================================"
  exit 0
fi
echo
echo "============================================================"
echo " Fertig. Starten: Symbol \"MobaLedLib Studio\" (Schreibtisch oder Anwendungsmenue)"
echo "         oder  $HERE/start_linux.sh"
echo " Beim ersten Doppelklick fragt der Dateimanager ggf. \"Ausfuehren\" / \"Starter vertrauen\"."
echo "============================================================"
exit 0
