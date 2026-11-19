Datei-Version: 1.00 (2026-11-19) - RELEASE_Hinweise_4.22.md
Gilt für webMobaLedLib 4.22

# webMobaLedLib 4.22

Anhänge dieses Releases: `webmobaledlib.zip` (Programm, mit `zip_erstellen.bat` Version 1.11 gebaut, `ROOT_IN_ZIP=1`), `START_HIER.txt` (erste Schritte), `ANLEITUNG_Installation.pdf` (Anleitung, Version 4.22) und `BETATEST_Checkliste.pdf` (Checkliste für Betatester, Version 3.11).
Installation: siehe `START_HIER.txt` und den Schnellstart der Anleitung. Aktualisieren: Menü **Hilfe → Update webMobaLedLib …**, danach das Programm **neu starten** und die Seite mit Strg+F5 neu laden.

## Wichtig beim Aktualisieren

- **Update von 3.92 oder älter:** Das ZIP enthält ab diesem Release `START_HIER.txt` im obersten Ordner. Der Update-Code bis 3.92 weist so ein ZIP ab („Das ZIP enthält nicht den Ordner python …“). Wer 3.92 oder älter hat, aktualisiert zuerst auf 3.93 und dann auf 4.22, oder lädt das ZIP von Hand (siehe Anleitung, Kapitel 7).
- **Nach dem Update das Programm neu starten** und die Seite neu laden. Oben darf keine rote Meldung stehen.
- **Neues Programmsymbol (4.10):** Für die Verknüpfung auf dem Desktop den Installer noch einmal ausführen.

## Neu seit Version 3.93 (3.94 bis 4.22)

**Verbinden:**
- Beim Start verbindet sich das Programm wieder mit der Lichtmaschine, die zuletzt verbunden war, sonst sucht es eine angeschlossene (Nano, ESP32, Pico) und verbindet, wenn es genau eine findet. Das läuft im Hintergrund. In den Programm Einstellungen abschaltbar (4.14).
- Nach „Setup übertragen“ wird mit der Lichtmaschine verbunden, auf die übertragen wurde, auch über WLAN (4.14).
- Neben „Mit Lichtmaschine verbinden“ steht ein Pfeil: Trennen, Neu verbinden, Board wechseln (4.14).
- Ohne eingestellten USB-Anschluss öffnet „Verbinden“ gleich „Board und USB Port erkennen“, danach wird automatisch verbunden (4.04).

**Speichern und Tabelle:**
- **Inkrementell speichern** (Strg+Umschalt+S, die Tastenkombination ist in den Programm Einstellungen einstellbar) sichert die ganze Arbeitsmappe mit fortlaufender Nummer; **Sicherungsdatei öffnen …** und **Sicherungsort ändern …** (4.15, 4.17).
- **Rückgängig und Wiederholen** in der Tabelle (Strg+Z, Strg+Y), die letzten 50 Änderungen je Blatt (4.02). Beim Beenden ohne Speichern lassen sich die verworfenen Änderungen beim nächsten Start wiederherstellen.
- **Spaltenbreiten übertragen** auf andere Seiten; Zellinnenabstand in den Programm Einstellungen (4.08).
- Weniger Platz im Kopfbereich (4.16, 4.19, 4.20, Issue 22).

**Einstellungen und Hilfe:**
- **Update Testversion:** eigener Link zu einer ZIP-Datei oder ZIP-Datei vom Rechner wählen (3.95).
- Neuer Reiter **ESP Einstellungen** (OLED-Modus 0 bis 5, Fotowiderstand, Zustandsspeicherung; Beitrag von moosbewohner) (3.94, 4.06, 4.09).
- Neues **Programmsymbol** (4.10).

**Erweiterungen (MLX):**
- Neuer Reiter **Erweiterungen** in den Optionen: Haken ein/aus, bekannte Erweiterungen werden von GitHub geladen und danach ohne Internet benutzt, eigene Erweiterungen hinzufügen (Name, Version oder Adresse), Rückfrage beim Öffnen einer Datei mit ausgeschalteter Erweiterung (3.96 bis 3.98).
- Name und Beschreibung aus der `libraries.json` (4.22). Neu importierte Erweiterungen lassen sich kompilieren, Einbindung mit `symlink://` (4.21). InfraredMLX auf dem Pico: IRremote 4.x statt 5.0 (4.05).

**Korrekturen:**
- „Board und USB Port erkennen“: richtiger Anschluss bei zwei angeschlossenen Arduinos, erkanntes Board bleibt eingestellt, Nano „neu“ und „Full“ werden unterschieden (3.98 bis 4.13, Issues 13 und 14).
- „Vorgang abbrechen“ beendet alles, der COM-Port ist sofort frei (4.12, Issue 15).
- Nach „Verwerfen“ beim Start reagiert die Spalte Aktiv sofort (4.11, Issue 16).
- ESP32: OTA-Passwort wird bei Bedarf abgefragt (4.03); Übertragen per USB mit WLAN ohne OTA (4.09).
- Versteckte Tabellen: das Startblatt erscheint nicht mehr als Reiter (4.07).
- Optionen: alle Reiter sichtbar (3.99).

**Noch nicht an Hardware oder im Browser geprüft:** Alles ab 4.11 (Verbinden beim Start, inkrementelles Speichern und seine Tastenkombination, Kopfbereich, Erweiterungen mit `symlink://`, Name und Beschreibung aus `libraries.json`) wurde nur gebaut und kompiliert, nicht auf Hardware oder im Browser getestet. IRremote 4.x für InfraredMLX ist nicht mit einem Pico geprüft. Die Übersetzungen der neuen Texte (CSV) sind ungeprüft.

**Wiki:** Paket `webmobaledlib_Wiki_Gesamt_Stand_4.22.zip` (39 Seiten, Hinweise in `LIESMICH_Wiki_Gesamt.md`). Die Bilder `erst_04_optionen.png` und `pg_09_verbinden.png` zeigen noch den alten Stand.

**Geplant:** Quell-URL direkt in der `platformio.ini` (Issue 6) ist nicht vorgesehen (Cache und `symlink://` bleiben); Rückfragen dazu stehen im Issue.

## Davor (3.66 bis 3.93)

Siehe RELEASE_Hinweise_3.93.md.
