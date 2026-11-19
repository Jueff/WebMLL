#!/usr/bin/env bash
# Datei-Version: 1.01 (2026-11-16) - build_simulator_linux.sh
# Baut libMobaLedLibWrapper.so (Simulator ohne Fenster) fuer Linux aus der Bibliothek MobaLedLib.
# Aufruf:  build_simulator_linux.sh [Ordner src der Bibliothek MobaLedLib] [Ausgabeordner]
# Voraussetzung: g++ (Paket build-essential)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIBSRC="${1:-$HERE/../libraries/MobaLedLib/src}"
ARCH="$(uname -m)"; case "$ARCH" in x86_64|amd64) ARCH=x64;; aarch64|arm64) ARCH=arm64;; armv7*|armv6*) ARCH=arm;; esac
OUT="${2:-$HERE/../Configuration/linux_$ARCH}"
[ -f "$LIBSRC/MobaLedLib.cpp" ] || { echo "Bibliothek nicht gefunden: $LIBSRC" >&2; exit 2; }
command -v g++ >/dev/null || { echo "g++ fehlt (Paket build-essential installieren)" >&2; exit 3; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cp -r "$LIBSRC" "$TMP/src"
# Get_Input ist in der Bibliothek 'inline' definiert; der Wrapper ruft es von aussen auf (MSVC erzeugt die Funktion trotzdem, g++ nicht)
sed -i 's/^inline int8_t MobaLedLib_C::Get_Input/int8_t MobaLedLib_C::Get_Input/' "$TMP/src/MobaLedLib.cpp"
# v1.01: Pruefen, ob alle Dateien des Ordners Arduino-stub da sind; FastLED.h wird hier selbst erzeugt (Gross-/Kleinschreibung der Dateinamen ist bei Updates und ZIP-Programmen unsicher)
for f in Arduino.h Arduino.cpp FastLEDStub.h FastLEDStub.cpp WString.h; do
    [ -f "$HERE/Arduino-stub/$f" ] || { echo "Datei fehlt im Ordner simulator_linux/Arduino-stub: $f (Programm bitte neu installieren oder aktualisieren)" >&2; exit 4; }
done
[ -f "$HERE/wrapper_linux.cpp" ] || { echo "Datei fehlt: $HERE/wrapper_linux.cpp" >&2; exit 4; }
mkdir -p "$TMP/inc"
printf '#include "FastLEDStub.h"\n' > "$TMP/inc/FastLED.h"
printf '#include "FastLEDStub.h"\n' > "$TMP/inc/FASTLed.h"
mkdir -p "$OUT"
g++ -shared -fPIC -O2 -std=gnu++17 -fpermissive -w -I"$TMP/src" -I"$TMP/inc" -I"$HERE/Arduino-stub" \
    -o "$OUT/libMobaLedLibWrapper.so" \
    "$TMP/src/AnalogPattern.cpp" "$TMP/src/Counter.cpp" "$TMP/src/House.cpp" "$TMP/src/Logic.cpp" \
    "$TMP/src/MobaLedLib.cpp" "$TMP/src/RandFunc.cpp" "$TMP/src/Schedule.cpp" "$TMP/src/WeldingLight.cpp" \
    "$HERE/Arduino-stub/Arduino.cpp" "$HERE/Arduino-stub/FastLEDStub.cpp" "$HERE/wrapper_linux.cpp"
echo "fertig: $OUT/libMobaLedLibWrapper.so"
