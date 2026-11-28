Datei-Version: 1.21 (2026-11-28) - RELEASE_Hinweise_5.65.md
Gilt für MobaLedLib Studio 5.65

# MobaLedLib Studio 5.65

Anhänge dieses Releases: `webmobaledlib.zip` (Programm, mit `zip_erstellen.bat` Version 1.11 gebaut, `ROOT_IN_ZIP=1`), `START_HIER.txt` (erste Schritte), `ANLEITUNG_Installation.pdf` (Anleitung, Version 5.65) und `BETATEST_Checkliste.pdf` (Checkliste für Betatester, Version 4.41).
Installation: siehe `START_HIER.txt` und den Schnellstart der Anleitung. Aktualisieren: Menü **Hilfe → Update MobaLedLib Studio …**, danach das Programm **neu starten** und die Seite mit Strg+F5 neu laden.

## Wichtig beim Aktualisieren

- **Update von 3.92 oder älter:** Das ZIP enthält ab diesem Release `START_HIER.txt` im obersten Ordner. Der Update-Code bis 3.92 weist so ein ZIP ab („Das ZIP enthält nicht den Ordner python …“). Wer 3.92 oder älter hat, aktualisiert zuerst auf 3.93 und dann auf 4.33, oder lädt das ZIP von Hand (siehe Anleitung, Kapitel 7).
- **Nach dem Update das Programm neu starten** und die Seite neu laden. Oben darf keine rote Meldung stehen.
- **Neues Programmsymbol (4.10):** Für die Verknüpfung auf dem Desktop den Installer noch einmal ausführen.

## Neu seit Version 3.93 (3.94 bis 5.65)

**Neu seit 5.60 (5.61 bis 5.65):**
- **Hardware Optionen: Lichtmaschine wählen (Pull Request 88 von Jürgen, dort 5.61 bis 5.70):** Im Reiter Lichtmaschine wird die Lichtmaschine wieder ausgewählt (Classic, Mini, Pro, Pico Zero, MoLLi, Uno), gruppiert nach Plattform. Bild und Protokolle folgen der Wahl (Mini ohne Protokoll, ohne DCC Arduino), ohne gespeicherte Wahl gilt die Vorgabe der Plattform. Ein Wechsel auf einen anderen Typ setzt den COM Port zurück und fragt nach der Suche; die Geräteauswahl zeigt nur passende Geräte, beim Pico sind andere MobaLedLib Geräte nach Rückfrage wählbar. Der Knopf heißt „Suchen“.
- **Erkennung über detectionRules und USB-Liste (Jürgen, 5.65):** Die USB-Kennungen der Plattformen stehen in `csv/Lichtmaschinen_prop.json` (detectionRules, je Lichtmaschine eigene Regel-Sets, zum Beispiel für den Uno). Neu im Menü Werkzeuge: **Liste der USB Geräte** (Kennung, Bezeichnung, passende Lichtmaschine, als Text kopierbar).
- **Log-Fenster mit Farben und Cursor (5.62, Pull Request 85 von Jürgen):** Beim Kompilieren und Hochladen erscheinen die Meldungen von PlatformIO mit Farben; Fortschrittsanzeigen werden an derselben Stelle aktualisiert.
- **Mainboard LEDs, Blattwechsel, Protokollfenster (5.63, Pull Request 86 von Jürgen):** Die Mainboard LEDs kommen bei Pro (ESP32) und Pico Zero aus der Konfigurationsdatei, SPI wird nicht mehr unterstützt. Beim Blattwechsel wird die Verbindung getrennt, wenn das Blatt zu einer anderen Lichtmaschine gehört. Bei Setup übertragen ist die Meldung am Anfang des Protokollfensters übersetzt.
- **Makrotext von Erweiterungen (5.64, Pull Request 87 von Jürgen):** Makros von Erweiterungen (zum Beispiel `EX.IRReceiverNEC(23, 0, 2)`) werden beim direkten Bearbeiten nicht mehr als ungültig abgewiesen; im Fehlerdialog löst Return „Änderung prüfen“ aus.
- **Verbinden mit besserer Fehlermeldung (5.61, Meldung eines Testers mit Uno):** Die Meldung unterscheidet, ob das Gerät nicht antwortet, unlesbare Zeichen sendet oder anders antwortet, und nennt den Knopf „Zum Arduino schicken“. Ein Uno ist von einem Nano mit neuem Bootloader nicht zu unterscheiden; bei einem Uno muss in den Optionen das Board Uno eingestellt sein, bevor das Programm geladen wird.
- **Zu prüfen:** Ohne Browser und ohne Hardware geprüft (Syntax und Tests ohne Oberfläche). Die neuen Dialoge (Hardware Optionen, Geräteauswahl, Liste der USB Geräte, Log-Fenster) bitte am besten mit echten Geräten testen; die Punkte 434 bis 451 der Checkliste beschreiben, was zu prüfen ist.
- **Nicht enthalten:** Pull Request 81 (gemeinsamer Uploadweg M08, moosbewohner): wird als Nächstes geprüft.

**Neu seit 5.54 (5.55 bis 5.60):**
- **LM-Ausgang (5.55 bis 5.58, Wunsch von Harold):** Der „LED Kanal“ heißt jetzt **LM-Ausgang** (Lichtmaschine Ausgang; ein Tooltip erklärt ihn). Die LED-Kette bleibt unverändert. Die Tabellenspalte heißt **LM-Ausgang**, ebenso das Feld im Servo-, DM-Servo- und Soundtest, im Raum-Dialog (dort auch „Anzahl RGB-LEDs“ statt „RGB-LED Kanäle“ und „Anzahl Räume“ statt „Anzahl“), im Parameterformular, im Servo- und im LED-Farb-Animations-Dialog (vorher „Anschluss-Kanal“). Die Einstellung heißt „Spalte LM-Ausgang in der Tabelle änderbar“. Die farbigen Knöpfe heißen **LED RGB-Anschluss Auswahl** (vorher „LED Kanal Auswahl“; sie wählen R, G oder B eines WS2811-Moduls und haben mit dem LM-Ausgang nichts zu tun). Die Felder haben Tooltips („Nummer des Lichtmaschinen Ausgangs“); die Wiki-Seite Begriffe erklärt **LM-Ausgang** und **LED RGB-Anschluss**.
- **Neues Makro (5.55):** Der LM-Ausgang ist mit dem der nächsten Zeile darüber voreingestellt (Makros mit eigenem Vorgabewert, zum Beispiel Taster, behalten ihn).
- **Serieller Monitor und Verbindung (5.59, Pull Request 82 von Jürgen):** Ein Verbindungsknopf; **Verbinden** testet zuerst kurz auf den EFFECT Mode, sonst liest der Monitor nur mit (DIRECT Mode). Verbindungsverlust (zum Beispiel USB abgezogen) wird erkannt („Verbindung verloren - Pro/COMx“), danach verbindet das Programm automatisch neu. Beim Verlassen des Monitors stellt das Programm die Verbindung wieder auf das Blatt um. **Setup übertragen** mit schnellem Upload nutzt die offene Verbindung.
- **Plattformen und Protokolle (5.59, Jürgen):** `csv/Lichtmaschinen_prop.json` mit devices, platforms und protocols; Firmware-Auswahl nach Plattform; die Bestätigung der LNet-Lizenz gilt nur für das eigene Blatt.
- **Weitere Korrekturen (5.59, Jürgen):** ESP32 schreibt die Mainboard_LED-Defines nicht in die Kopfdatei; Doppelklick auf Name und Beleuchtung öffnet die Makroauswahl auch bei altem gespeicherten Schalter; die Ein/Aus-Tasten gleicher Adresse sind nach Setup übertragen alle eingeschaltet; die Kopfdatei enthält beim schnellen Update die Eingangskanal-Defines in den MLLDYN-Marken.
- **ESP32: Mainboard_LED (5.60, Pull Request 83 von Jürgen):** Das Makro schaltet die drei Status-LEDs der Hauptplatine (vorher passierte nichts). Die Firmware ist nicht kompiliert und nicht am Board geprüft.
- **Zu prüfen:** Alles ist ohne Browser und ohne Hardware geprüft (Syntax und Tests ohne Oberfläche). Jürgens Tests für den Seriellen Monitor liefen hier nicht (das Modul serial fehlt). Die Checkliste für Betatester hat dazu die Punkte 417 bis 433.

**Neu seit 5.41 (5.42 bis 5.54):**
- **Menü Werkzeuge (5.49, Wunsch von Jürgen, Issue 75):** Zwischen Einstellungen und Hilfe steht das Menü **Werkzeuge** mit Datenübertragung, Firmware installieren …, ESP32-Firmware über WLAN hochladen … und Wartung … (Entwicklungsumgebung, PlatformIO, Bibliotheken). Diese Funktionen stehen nicht mehr in Einstellungen und Hardware Optionen. Im Anfänger Modus ist das Menü ausgeblendet.
- **LED Kanal (5.51, 5.52):** In den Dialogen der Makros mit LEDs steht der **LED Kanal oben**. Im Raum-Dialog steht der Haken **Individuelle Zeiten** über den Reglern. Neue Einstellung **Spalte LED/Sound Kanal in der Tabelle änderbar** (Programm Generator, Vorgabe aus): Die Spalte lässt sich dann in der Tabelle ändern und nach unten ausfüllen, die Start LedNr werden neu berechnet. Der Anwender ist selbst für richtige Werte verantwortlich.
- **Servo-Hilfetext (5.51):** Deutsch „Programm Servo Einstellungen“ statt „Servo_Pos Programm“ (Excel-Mappe und csv).
- **Zeilen 1 und 2 geschützt (5.50, Issue 77):** „Zeile einfügen“, „Zeilen löschen“ und „Zeilen verschieben“ verändern sie nicht mehr.
- **Verbindung (5.46 bis 5.48, Pull Request 76 von Jürgen):** Neben dem Knopf steht Typ und Anschluss („Verbunden mit Pro/COM3 - EFFECT Mode“), mit Verbindung heißt der Knopf „Trennen“. Eine negative Zahl im Anschluss der Tabelle (zum Beispiel -7, von Excel gesetzt) ist ein Hinweis auf COM7; „-7“ wird nicht mehr als Anschluss COM-7 benutzt. Pro Gerät gibt es nur eine Verbindung. Strg+C beendet das Programm ohne Fehlermeldung. Setup übertragen ohne eingetragenen Anschluss brach mit „vb2py.logger has no attribute warning“ ab (behoben).
- **Datenübertragung (5.53, Pull Request 78 von moosbewohner):** Quelladresse ohne `http://` mit Portfeld (Vorgabe 45875); der Verbindungscode braucht nur noch sechs Zeichen.
- **Selectrix, Anschluss-Hinweis, Firmware (5.54, Pull Request 80 von Jürgen):** Selectrix: Channel 1 bis 99, Bitposition 1 bis 8 (Eingabe und Header); DCC, LNet und CAN: Adresse 0 nicht erlaubt. Der Anschluss-Hinweis (-3) wird auch bei Setup übertragen und Hochladen ausgewertet. Geräteauswahl: kein `COM?` mehr, OK ohne Auswahl ändert nichts, Abbrechen schließt das Übertragungsfenster; Firmware installieren (Pico) mit eigener Auswahl, lokale ZIP-Datei für die Firmware. Das Fenster Kompilieren und Hochladen ist verschiebbar. PGF-Import in ein verstecktes Blatt blendet es ein.
- **Weiteres (5.42 bis 5.45):** Startseite: Pico Zero bietet nur DCC an; Mini und MoLLi zeigen ihr eigenes Bild. Geräteauswahl: Seriennummer bei Pico-Geräten (5.44, Jürgen). Die Einstellung „Startseite beim Programmstart anzeigen“ steht unter Allgemein.
- **Zu prüfen:** Alle Punkte sind ohne Browser und ohne Hardware geprüft (Syntax und Tests ohne Oberfläche). Die Checkliste für Betatester hat dazu die Punkte 410 bis 416.
- **Nicht enthalten:** Pull Request 79 (gemeinsamer Uploadweg M08, moosbewohner): noch nicht übernommen, der Entwickler bat um Neuaufbau auf diesen Stand.

**Neu seit 5.39 (5.40, 5.41): Übernahme des offiziellen Release MobaLedLib 3.6.0**
- Das Programm meldet sich als „Ver. 3.6.0“ (ohne Zusatz wie L3). Die Bibliothek hat die Version 3.6.0 (`library.properties`), die `platformio.ini` nennt `MobaLedLib@3.6.0`; die Tabelle Libraries der mitgelieferten Excel-Mappe `csv/Prog_Generator_MobaLedLib.xlsm` (Stand 3.6.0) verlangt diese Version.
- Der Vergleich mit dem Paket `Ver_3.6.0` ergab sonst keine Änderungen: Makrotabelle, Parameter und Plattformen sind gleich, die Dateien in `LEDs_AutoProg` sind im Release älter als unsere (die Erweiterungen für OTA, WLAN-Anzeige und Identify bleiben). Neu ist das Beispiel `AddressLearn.MLL_pgf` (braucht die Erweiterung AddressLearnMLX).
- Die `README.md` der Bibliothek (`libraries/MobaLedLib`) ist die Fassung von 3.6.0 (5.41). Der Entwickler hat die Bibliothek mit GitHub verglichen: `PicoFastLED.h` bleibt bei unserer neueren Fassung, alle anderen Dateien sind gleich.
- **Zu prüfen:** Timeout (Mindestwert 0 oder 1) im Pattern Configurator und vier abweichende Beispielbilder in `Pattern_Config_Examples`. Nur gebaut und kompiliert, nicht an Hardware geprüft.

**Neu seit 5.25 (5.26 bis 5.39):**
- **Startseite überarbeitet (5.34 bis 5.36):** Zuerst wählt man die **Lichtmaschine**, dann zeigt das Programm nur die Zentralen, die sie unterstützt. Fünf Kacheln: Classic (Nano, alle Zentralen), Mini (Nano, nur DCC), Pro (ESP32, alle), Pico Zero (Pico, alle) und MoLLi (Pico, nur DCC). Alle Kacheln sind gleich groß, die Seite spricht mit Du. Die Lichtmaschinen stehen in `csv/Lichtmaschinen_prop.json`; ein neues Produkt wird nur dort ergänzt. Die Startprogramme `*.MLL_pgf` im Ordner `Startprogramme` liefert Harold noch.
- **Logic (5.26 bis 5.29):** Neues Eingabefenster für die logische Verknüpfung (UND, ODER, nicht) mit Vorschau in Klartext und Prüfung. Eingänge in Gruppen: Eingang dieser Zeile, Variablen der Tabelle, Schalter A bis D (1 bis 250), eigener Name. Das Fenster öffnet auch, wenn in der Tabelle Makros mit Parametern wie On_Min stehen.
- **Hardware Optionen und Geräteauswahl (5.30, Jürgen, Pull Request 72):** Der Reiter Lichtmaschine zeigt Hardware, Port und Bild. „Erkennen“ öffnet die Geräteauswahl mit Typ, Port, Version und USB Kennung, auch für andere MobaLedLib-Geräte; belegte Anschlüsse stehen als „blockiert“. Bootloader des Nano wird erkannt, ESP32 mit Displaytyp, Einstellungen (Protokoll, Lichtsensor, Schaltzustände speichern) im Blatt gespeichert.
- **Tabelle bedienen wie in Excel (5.31, Jürgen, Pull Request 73):** Pfeiltasten beenden die Eingabe und wechseln die Zelle, Doppelklick auf Name und Beleuchtung öffnet die Makroauswahl, die Markierung bleibt nach Dialogen und Bearbeiten.
- **Selectrix wieder da (5.33, Jürgen, Pull Request 74):** Protokoll eines Blatts auf Selectrix umstellbar, Adressen werden umgerechnet, Channel und Bitposition werden geprüft.
- **Farb Test (5.37):** Knopf „Farb Test beenden“ unten rechts; Set_ColTab öffnet den Farb Test auch ohne angeschlossene Lichtmaschine.
- **Eingabefenster der Makros (5.37):** Flags (Optionale Zähler Parameter, Mode, RandMode) wählt man in einer aufklappbaren Liste mit Haken.
- **Korrekturen:** Entf löscht ohne Meldung „Es läuft noch ein Vorgang“ (5.32). Ohne angeschlossene Lichtmaschine erscheint „Fehler beim Öffnen der Verbindung“ beim Reiterwechsel nur einmal (5.38). Makro Button: kein Fehler „Parameter … nicht gefunden“ mehr, wenn die Bibliothek aus der xlsm geladen wird und eine Zelle einen Kommentar hat (5.39).
- **Geprüft:** 5.31, 5.32, 5.33, 5.36, 5.38 und 5.39 hat der Entwickler im Browser bestätigt. Nur gebaut und kompiliert: Logic (5.26 bis 5.29), Hardware Optionen und Geräteauswahl (5.30), Startseite 5.34/5.35, Flags-Auswahl (5.37). Übersetzungen der neuen Texte gibt es nur Deutsch und Englisch.

**Neu seit 5.12 (5.13 bis 5.25):**
- **Startseite für Einsteiger (5.23, 5.24):** Beim Start fragt MobaLedLib Studio nach der **Modellbahnzentrale** (DCC, Selectrix, LNet, Märklin CAN-Bus oder ohne Zentrale) und der **Lichtmaschine** (Classic / Mini, Pro, Pico Zero / MoLLI; auch „Automatisch erkennen“). Mit **Anfangen** blendet das Programm die Tabellen der anderen Zentralen aus, öffnet die richtige Tabelle, lädt das Startprogramm aus dem Ordner `Startprogramme` (sofern vorhanden) und stellt das Board ein. Die Seite erklärt den Weg mit **Setup übertragen** und **Dialog Wizard**. Im Anfänger Modus steht ein Hinweis darunter. Ausschalten mit dem Haken auf der Seite oder unter Einstellungen → Allgemein → „Startseite beim Programmstart anzeigen“. Die Texte gibt es zunächst nur auf Deutsch. **Die Startseite ist noch nicht im Browser geprüft.** Wiki: Seite `startseite`.
- **Eingabefenster der Taster-Makros (5.19 bis 5.22, Anregung im Forum von PeterVT11):** Farben mit der Taste **Farbe wählen** (Mini-Farbtest, LED-Nummer 0, Kanal 0, es leuchtet nur die Heartbeat-LED), die Zahlen bleiben als Text änderbar, daneben ein Farbfeld. Werte 0/1 sind Ein/Aus-Schalter. Das Feld heißt „Zielvariable“, wenn es nur eine gibt; der Tooltip erklärt Test0, Test1, Test2.
- **Fehler beim Speichern eines Makros (5.20):** Eine ungültige Eingabe (zum Beispiel keine Zielvariable) wurde trotz Fehlermeldung gespeichert. Jetzt erscheint das Eingabefenster wieder; die Meldung nennt den Namen des Eingabefeldes.
- **Pico (5.15 bis 5.17, Beitrag von Jürgen, Pull Request 71, Issue 70):** Kein Abbruch mehr mit „no member named showColor“ (auch bei einer alten Kopie der Bibliothek in `.pio`). Ändert sich der COM-Port nach dem Hochladen, findet das Programm ihn wieder und trägt ihn ein. Meldet die Firmware einen Fehler, bricht die Übertragung mit verständlicher Meldung ab.
- **Board und USB Port erkennen (5.18, Pull Request 39):** Der Hinweis zum Knopf beschreibt die Suche nach Nano, ESP32 und Pico, in allen Sprachen.
- **Protokoll-Fenster (5.14, Issue 60):** Die Knöpfe „Vorgang abbrechen“ und „Schließen“ flackern nicht mehr. **Von Jürgen noch nicht bestätigt.**
- **Windows (5.13):** Beim Übertragen öffnen sich keine kurzen schwarzen Konsolenfenster mehr.
- **Begriff LocoNet (5.25):** Der geschützte Begriff steht nicht mehr in der Oberfläche und im Wiki, es heißt „LNet“. Der offizielle Lizenzdialog bleibt unverändert.

**Neu seit 4.98 (4.99 bis 5.12):**
- **Neuer Name MobaLedLib Studio (5.08, 5.09, 5.10):** Kopfzeile, Browser-Tab, Meldungen (auch Installation und Reparatur), Anleitung, Checkliste und Wiki heißen jetzt „MobaLedLib Studio“, in allen Sprachen. Das Desktop-Symbol heißt ebenfalls „MobaLedLib Studio“: Die Installationsskripte (Windows, Linux, macOS, Raspberry Pi) legen es neu an und entfernen die Symbole mit den alten Namen. **Dafür das Installationsskript einmal erneut ausführen** (nach einem Update über das Menü bleiben die alten Symbole bis dahin). Technische Namen bleiben: Dateinamen (`webmobaledlib.py`, `webmobaledlib.zip`), Datenordner `webMobaLedLib`, Update-Verfahren.
- **Parameterformular der Makros (5.04 bis 5.06):** Zahlenwerte haben einen Schieberegler mit Zahlenfeld und den Tasten − und +; das Zahlenfeld (auch LED Channel) lässt sich direkt eintragen und mit dem Mausrad ändern. Zeitwerte werden in den Feldern Min, Sek und ms eingegeben. Der Farbwert im HSV-Farbraum hat einen Regler im Farbverlauf und ein Feld mit der Farbe. Die LED Kanal Auswahl hat farbige Tasten (Gelb, Zyan, Rot, Grün, Blau). Der Hinweistext zum HSV-Farbwert nennt die Regenbogen-Zahlen (0 Rot, 32 Orange, 64 Gelb, 96 Grün, 128 Zyan, 160 Blau, 192 Violett, 224 Pink) (5.10).
- **Formular für House und GasLights (5.07):** Anzahlen und Zeiten mit Regler, Zahlenfeld, − und + und Mausrad; LED Kanal als Zahlenfeld.
- **Board und USB Port erkennen (5.02, Beitrag von Jürgen, Pull Request 39, Issue 35):** Findet die Erkennung mehrere verschiedene Lichtmaschinen, kann man vorher das Modell wählen.
- **Zentrale erkennen (4.99, Beitrag von Jürgen, Pull Request 61):** Im Dialog „Auswahl des COM Ports“ blinken die LEDs der gewählten Zentrale (ESP32, Pico). Die neue Firmware muss dafür einmal ganz übertragen werden. Der Pico bekommt die Konfiguration auch, wenn er nach dem Hochladen einen anderen COM Port hat.
- **Überzählige LEDs (5.00, Beitrag von Jürgen, Pull Request 63, Issue 62):** Hängen am Strang mehr LEDs, als konfiguriert sind, werden sie beim Start ausgeschaltet (Setup einmal ganz neu übertragen).
- **Schnelles Update nach Programm-Update (5.03, Beitrag von Jürgen, Pull Request 66, Issue 64):** Nach jedem Update wird beim ersten „Setup übertragen“ einmal die ganze Firmware übertragen.
- **Testtasten (5.01, Issue 68):** Startwert 1 schaltet alle Ein/Aus-Tasten derselben Adresse ein.
- **Niederländisch (5.11, Rückmeldung eines Testers):** Menü „Uitbreidingen …“; Hinweise (Tooltips) in den Einstellungsfenstern in der gewählten Sprache, fehlende Übersetzungen ergänzt.
- **Hilfe und Wiki (5.12):** Hilfe → Hilfe öffnen und die Hilfe-Knöpfe (OTA, Servo-Animation, Timeline Editor) führen zu den Seiten im Wiki-Kapitel `anleitungen:mobaledlibstudio`; die Wiki-Seiten des Pakets verweisen auf diesen Namensraum.
- **Firewall-Text (5.10):** Der Hinweis zur Windows-Firewall nennt die Regel „webMLL Server <Port>“.

**Neu seit 4.93 (4.94 bis 4.98):**
- **Neuinstallation mit git (4.98):** `install_windows.bat` (mit winget; `/nogit` überspringt es) und `install_mac.command` installieren jetzt git mit, das PlatformIO für ESP32 und Pico braucht. Fehlt git trotzdem, fragt das Programm beim Übersetzen für ESP32 oder Pico „git jetzt installieren?“, auch im Anfänger Modus. Bisher musste man git nachträglich in den Optionen (Entwicklungsumgebung) installieren.
- **ESP32 startet nach dem Hochladen endlos neu (4.97):** Ein altes Dateisystem (LittleFS) im Flash ließ die Firmware beim Start abstürzen („lfs_fs_grow_ assert failed“). Nach dem vollständigen Hochladen per USB löscht das Programm jetzt die Dateisystem-Partition, danach kommt die Konfiguration.
- **Laden einer Datei mit mehreren Tabellenblättern (4.96):** Bei der Frage „Soll die Seite … importiert werden?“ gibt es den Knopf „Ja, alle“.
- **Feste IP-Adresse und USB-Anschluss beim ESP32 (4.95, Meldung aus dem Forum):** Die feste IP-Adresse gilt auch in der minimalen Firmware (ESP32-Setup per OTA). Ein nicht vorhandener USB-Anschluss wird vor dem langen Build gemeldet („Board und USB Port erkennen“). Die Adresse des eigenen Rechners wird als Adresse des ESP32 abgelehnt; bleibt „Adresse für WebMLL“ leer, gilt die feste IP.
- **PlatformIO-Build-Verzeichnis (4.94, Pull Request 54):** Das Build-Verzeichnis für ESP32 wird in `headless_esp32_ota` einheitlich ermittelt (mit Test `test_esp32_build_directory.py`). Das Zusammenführen der Build-Wege (Programmgenerator, OTA, Patterngenerator) ist für später geplant.
- **Hardware geprüft (Rückmeldung):** Pico-Auswahl und Verbindung per WLAN beim Blattwechsel (4.90 bis 4.92) funktionieren.

**Neu seit 4.79 (4.80 bis 4.93):**
- **Mini-Farbtest in der grafischen Ansicht (4.83):** F3 oder Rechtsklick bei einem ConstRGB-Makro, wie in der Tabelle. Bei anderen Makros sendet der Mini-Farbtest beim Öffnen nichts, erst nach „Blinken“ oder einer Farbänderung (4.82).
- **Tabelle (4.84 bis 4.88):** Beim Einfügen springt die Anzeige nicht mehr. Nach Einfügen, Löschen, Duplizieren und Verschieben ist die betroffene Zeile markiert, mehrfaches Löschen geht hintereinander.
- **Datenübertragung (4.89, Pull Request 57, moosbewohner):** Neuer Menüpunkt „Datenübertragung“: Tabellen von einem Rechner auf einen anderen übertragen, gesichert mit Verbindungscode; vor dem Überschreiben entsteht eine Sicherung. Beschreibung in `DATENUEBERTRAGUNG.md`. Getestet unter Windows 10, Windows 11 und Raspberry Pi 4B. Bei falschem Verbindungscode erscheint eine verständliche Meldung (4.93).
- **Kompilieren und Hochladen (4.90, Issue 60):** Die Knöpfe flackern nicht mehr.
- **Pico-Firmware (4.90, Issue 58):** Sind mehrere Picos angeschlossen, fragt das Programm, welcher bespielt werden soll.
- **Verbindung folgt dem Tabellenblatt (4.90 bis 4.92, Issue 59):** Beim Blattwechsel verbindet sich das Programm mit der Lichtmaschine des Blattes (USB und WLAN); Trennen, Neu verbinden und Board wechseln gelten für das aktuelle Blatt.

**Tabelle und Farben (4.55 bis 4.66, 4.73):**
- **Farben kopieren und einfügen (4.55):** Strg+C, Strg+X und Strg+V übertragen auch die Feldfarbe, bei Zellen und ganzen Zeilen; ist das Ziel größer, wird das Muster wiederholt. „Nur Text einfügen“ (Strg+Umschalt+V oder Rechtsklick) fügt ohne Farbe ein. Von Hand gesetzte Farben sind vor den Färberegeln geschützt, bleiben mit der Tabelle gespeichert und lassen sich zurücknehmen. Farbe entfernen (4.57): die Zelle wird wieder nach den Färberegeln gefärbt.
- **Mini-Farbtest für ConstRGB (4.58 bis 4.61, Idee eines Anwenders):** Zelle Beleuchtung anklicken, F3 drücken oder Rechtsklick „Farbe mit Mini-Farbtest ändern …“. Die Farbe leuchtet live an der LED der Tabellenzeile; mit OK ersetzt das Programm die Zahlen im Makrotext, Strg+Z nimmt es zurück. F3 öffnet nicht mehr die Suche des Browsers (4.65, 4.66).
- **Tabelle drucken (4.62 bis 4.64):** Menü Datei, „Tabelle drucken …“: Spalten wählen (je Tabelle gemerkt), Zeilennummer und Farben ein oder aus, Zeilen: alle, markierte oder ein Zeilenbereich. Druckansicht in Querformat A4 mit Kopfzeile auf jeder Seite, gedruckt wird über den Druckdialog des Browsers (auch „Als PDF speichern“).
- **Tabelle färben (4.73):** Die Felder „Farbe“ zeigen die Farbe selbst, nicht nur den Farbcode.

**Hardware Optionen und Kopfzeile (4.67 bis 4.79):**
- Der Dialog heißt **Hardware Optionen**. Im Anfänger Modus sind die Reiter Entwicklungsumgebung und Firmware Installation nicht sichtbar. Boardnamen: „Lichtmaschine Classic, Mini (Nano (neue Version))“, „Lichtmaschine Pro (ESP32)“, „Lichtmaschine Pico Zero, MoLLi (Raspberry Pico)“. **PlatformIO (Standard)** steht zuerst, „ARDUINO-IDE (nur Kompatibilität – nicht mehr nutzen)“; der Knopf „ARDUINO-IDE Einstellungen“ erscheint nur mit ARDUINO-IDE. Die Reiter ESP Einstellungen und WLAN (OTA) erscheinen nur mit ESP32. Die Adresse /ARDUINOEinstellungen entfällt (4.68, 4.69).
- **ESP32-Konfiguration über WLAN (4.71, Pull Request 54, moosbewohner):** Mit „Schnelles Update“ und PlatformIO wird die Konfiguration auch über WLAN übertragen (gesicherter Kanal mit dem OTA-Passwort, bis zu drei Versuche, Nachprüfung). Die Firmware muss einmal per USB oder OTA aufgespielt sein; der Pico bleibt bei USB.
- **Speichern unter … (4.72):** Bietet der Browser keine Auswahl des Speicherorts (Zugriff über das Netz per http, Firefox), fehlt der Knopf „Speichern unter …“; ein Hinweis erklärt den Grund, die Datei geht in den Downloads-Ordner.
- **Kopfzeile (4.74):** Meldung des Programms in der Menüzeile neben „Zwischengespeichert“, Verbindungsstatus neben dem Knopf „Mit Lichtmaschine verbinden“; die Knöpfe oben rechts springen nicht mehr. Textfehler korrigiert (Sound-Datei, Programm Einstellungen, Standardschrift).
- **Dunkles Farbschema (4.75, Beitrag von moosbewohner, Pull Request 55):** Hellere, abgestufte Flächen für Dialoge, Eingabefelder und die Tabelle bei „Dunkel mit Tabelle“.
- **Port-Auswahl (4.76, Issue 37):** Nach dem Wechsel des Boards über „Andere Typen“ ändern sich Bild, Beschreibungstext und roter Hinweis.
- **Startmeldung der Lichtmaschine (4.77, Issue 30):** Das Datum steht als TT.MM.JJ, unabhängig von der Spracheinstellung des Rechners (Setup neu übertragen).
- **Dialoge und Menüs (4.77, Issue 34):** CSS-Absicherung, damit sie fest über der Seite liegen (Mac; Rückmeldung des Anwenders steht aus).
- **Simulator (4.78, Issue 45):** Eine gespeicherte Fensterlage außerhalb des Bildschirms (−32000 eines minimierten Fensters) wird nicht mehr gespeichert und beim Öffnen auf 800/400 zurückgesetzt.
- **ESP32: DHCP oder feste IP-Adresse (4.79, Anregung aus dem Forum):** Im Reiter WLAN (OTA) der Hardware Optionen wählt man „DHCP“ oder „Statische IP-Adresse“ (IP-Adresse, Gateway, Subnetzmaske, DNS-Server). Die Eingaben werden geprüft. Nach der Umstellung das ESP32-Setup einmal neu übertragen und bei „Adresse für WebMLL“ die neue IP-Adresse eintragen. Nicht enthalten: verstecktes WLAN, mehrere WLANs. Noch nicht an Hardware geprüft.

**Menüs neu geordnet (4.51 bis 4.67, Vorschlag von Michael aus dem Forum):**
- Neues Menü **Einstellungen** zwischen **Tabelle** und **Hilfe**: Allgemein, Programm Generator, Farb Test, Simulator (nur Experten Modus), Netzzugriff, Spezial, Erweiterungen …, Einstellungen sichern …, Einstellungen übernehmen …. Die Seite **Programm Einstellungen** ist kein Reiter mehr, die Einträge springen zur Gruppe.
- **Tabelle, Tabelle färben …** öffnet die Seite mit den Bedingungen für die Zeilenfarben (früher Reiter **Tabelle Färben**, Titel jetzt „Tabelle färben“). Der Knopf **Zeilen Färben** und die Option „Zeilen Färben Button verstecken“ entfallen.
- Das Menü **Lichtmaschine** entfällt: Der Pfeil neben **Mit Lichtmaschine verbinden** enthält Verbinden, Verbindung trennen, Neu verbinden, Board wechseln …, Alle LED aus.
- **ARDUINO Einstellungen** ist ein Fenster mit Speichern und Abbrechen (Optionen, Reiter Entwicklungsumgebung, Knopf **ARDUINO-IDE Einstellungen**). **ESP32-Firmware über WLAN hochladen …** steht als Knopf auf dem Reiter WLAN (OTA) der Optionen. **Erweiterungen** ist ein eigenes Fenster (Haken sofort wirksam, Schließen), der Reiter in den Optionen entfällt. **Importieren v. altem Programm …** steht im Menü **Datei**, der Reiter **Dateien** in den Optionen entfällt.
- Schritt 2 (ab 4.67): Der Knopf **Optionen Werkzeuge** heißt **Hardware Optionen**, der Reiter **Bootloader** heißt **Firmware Installation** und enthält auch den Knopf **Firmware installieren** (vorher im Reiter Lichtmaschine). Reste der alten Reiter werden später entfernt.

**Darstellung (4.44 bis 4.49, Issue 51):**
- **Darstellung der Oberfläche** (Programm Einstellungen, Allgemeine Einstellungen, unter Sprache): Hell (Vorgabe, bisheriger Stil), Hell mit Kontrast (kräftigere Blattreiter, dunklere Hinweistexte), Dunkel (die Tabelle bleibt hell), Dunkel mit Tabelle (auch Tabellen dunkel, fest eingestellte Farben bleiben) oder Wie System.
- Blattreiter besser lesbar, Beschreibungstexte und Tooltips im Dunklen Modus lesbar (4.44 bis 4.49). Der Hinweis zu „Minimale/Maximale Zeit“ nennt die House()-Funktion, die Schrifteinstellungen erklären, wo welche Schrift wirkt (4.49).

**Speichern und Verbinden (4.42 bis 4.50):**
- „Kein ESP-Port gewählt“ (Issue 50): Ist die Lichtmaschine verbunden und in der Tabelle kein Anschluss eingetragen, nimmt das Programm den Anschluss der aktiven Verbindung (auch beim ESP32-Setup per USB mit WLAN). Bei mehreren Boards entscheidet die Einstellung „Kein Anschluss in der Tabelle: bei mehreren Boards“ (4.42, 4.43).
- Workbook-Dateinamen mit Datum und Uhrzeit (MobaLedLib_2026.11.20_20.05.03.json) bei „Workbook speichern als“ und „Inkrementell speichern“; die laufende Nummer entfällt (4.50).
- Beim Trennen gehen die LEDs der Anlage nicht mehr aus. Wer es möchte, setzt „Beim Trennen alle LEDs ausschalten“ (Allgemeine Einstellungen, Vorgabe aus) (4.50).

**Verbinden:**
- Beim Start verbindet sich das Programm wieder mit der Lichtmaschine, die zuletzt verbunden war, sonst sucht es eine angeschlossene (Nano, ESP32, Pico) und verbindet, wenn es genau eine findet. Das läuft im Hintergrund. In den Programm Einstellungen abschaltbar (4.14).
- Nach „Setup übertragen“ wird mit der Lichtmaschine verbunden, auf die übertragen wurde, auch über WLAN (4.14).
- Neben „Mit Lichtmaschine verbinden“ steht ein Pfeil: Trennen, Neu verbinden, Board wechseln (4.14), ab 4.51 auch Verbinden und Alle LED aus.
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

**Einstellungen auf einen anderen PC (4.24, Issue 29):**
- **Datei → Einstellungen sichern …** packt Programm Einstellungen, Farbtest/Palette, Erweiterungen und ESP32-OTA in eine ZIP, auf Wunsch auch die Tabellen. **Einstellungen übernehmen …** liest sie auf dem anderen PC ein (Übernahme beim nächsten Start, die alten Einstellungen werden gesichert). Passwort, Netzzugriff, USB-Anschluss und Fensterlage bleiben am PC.

**Bedienung (4.23 bis 4.26):**
- Das Kontextmenü (Rechtsklick) bleibt im sichtbaren Fenster (4.23).
- Log-Fenster: Schließen-Knopf nach dem Ende, Abbrechen nur solange etwas läuft (4.25, Issue 28).
- Bilder von Nano und Pico waren vertauscht, jetzt richtig (4.25, Issue 27).
- Fehler „slot stack … is empty“ nach „Board und USB Port erkennen“ behoben (4.26).
- **Paketliste (Issue 26):** `DATEIEN_IM_PAKET_Issue26.md` nennt Dateien, die das Programm selbst erzeugt und nicht ins Paket gehören; offene Punkte entscheidet der Entwickler.

- **Korrektur (4.41):** In 4.38 bis 4.40 baute sich die Seite wegen eines Fehlers bei den neuen Tastenkürzeln nicht mehr auf; behoben. Alle Funktionen von 4.37 bis 4.41 sind ab diesem Release enthalten.
- **Makro in Spalte L direkt bearbeiten (4.40, Beitrag von Jürgen, Issue 42):** Der Makrotext wird beim Bearbeiten sofort geprüft (Klammern, leere Parameter, Parameterzahl). Bei einem Fehler: „Originaltext wiederherstellen“ oder „Weiter editieren“. Nach einer gültigen Änderung werden Name und Symbol und die Felder LEDs, InCnt, LocInCh, Adressen, Testtasten und Start-LEDs neu gesetzt. Rückgängig und Wiederholen funktionieren.
- **Übertragungsfenster schließt automatisch (4.40, Issue 41):** Programm Einstellungen, Allgemeine Einstellungen: nach Erfolg (Vorgabe 5 Sekunden) und nach Fehler (Vorgabe 30 Sekunden), wählbar sofort, 5, 10, 30 Sekunden oder nie.
- **Fehler „Adresse mit zwei Typen“ (4.39, Issue 48):** Eine Adresse, die mit zwei verschiedenen Typen benutzt wird (zum Beispiel AnAus und Rot), wird beim Erzeugen der Kopfdatei wieder gemeldet; das Kompilieren startet dann nicht. Das gilt auch für andere Fehler in der Tabelle (zum Beispiel Adresse außerhalb des Bereichs), die bisher unbemerkt blieben.
- **Tastenkürzel (4.38, Issue 49):** Strg+Z (Rückgängig), Strg+Y oder Strg+Umschalt+Z (Wiederholen) gelten auf der ganzen Seite. Strg+S speichert dauerhaft (Menü Datei → Speichern), wie im Excel-Programm.
- **Schnelles Update: LED-Pins und LED-Gruppen (4.37, Beitrag von Jürgen, Issue 46):** Auch die Controller-Zuordnung gehört zur Konfiguration; eine Änderung braucht keinen vollständigen Upload.
- **Schnelles Update für ESP32 und Pico (4.36, Beitrag von Jürgen, Issue 31):** Neuer Haken „Schnelles Update“ im Reiter Entwicklungsumgebung. Mit Haken wird das Programm nur noch hochgeladen, wenn es nötig ist (erster Upload, geänderter Quellcode, Erweiterung oder Einstellung); sonst geht nur die Konfiguration in wenigen Sekunden zur Lichtmaschine. Bei Abweichung, fehlender Antwort oder Ablehnung wird komplett hochgeladen. Ohne Haken wie bisher; Nano und Uno unverändert. Auf ESP32 und Pico getestet.
- **Tooltips (4.34):** Im Dialog der Raumeffekte (Haus) und der Straßenbeleuchtung erscheinen die Tooltips wie im Excel-Programm, an den Effekt-Knöpfen und an den Feldern, in der Sprache des Programms.
- Nach einem Fehler beim Verbinden blieb „Es läuft noch ein Vorgang“ dauerhaft stehen und blockierte alle Eingaben; behoben (4.35, Rückmeldung zu 4.22).

**Übertragen auf den ESP32 und Hänger (4.27 bis 4.33):**
- Minimale Firmware per USB (Reiter OTA) nimmt keine Daten mehr aus der DCC-Tabelle, nur die Heartbeat-LED (4.29). „Schließen“ im Protokoll-Fenster funktioniert nach dem Upload (4.27).
- Beim Kompilieren und Hochladen auf den ESP32 erscheint die Ausgabe sofort im Protokoll-Fenster, und „Vorgang abbrechen“ beendet den Build (4.33).
- „Setup übertragen“ blieb bei einer Zeile wie `Counter(…)` ohne Zielvariable ohne Meldung stehen (Endlosschleife, 4.31) und stürzte mit Zielvariable ab (4.32). Beides behoben.
- Hilfe zur Fehlersuche: Steht ein Befehl länger als 25 Sekunden, schreibt das Programm den Zustand an `hang_dump.txt` im Datenordner (4.28, 4.30). Beim Kompilieren entsteht dabei ein Eintrag, das ist normal.

**Korrekturen:**
- „Board und USB Port erkennen“: richtiger Anschluss bei zwei angeschlossenen Arduinos, erkanntes Board bleibt eingestellt, Nano „neu“ und „Full“ werden unterschieden (3.98 bis 4.13, Issues 13 und 14).
- „Vorgang abbrechen“ beendet alles, der COM-Port ist sofort frei (4.12, Issue 15).
- Nach „Verwerfen“ beim Start reagiert die Spalte Aktiv sofort (4.11, Issue 16).
- ESP32: OTA-Passwort wird bei Bedarf abgefragt (4.03); Übertragen per USB mit WLAN ohne OTA (4.09).
- Versteckte Tabellen: das Startblatt erscheint nicht mehr als Reiter (4.07).
- Optionen: alle Reiter sichtbar (3.99).

**Noch nicht an Hardware oder im Browser geprüft:** (die Funktionen 4.55 bis 4.93 hat der Entwickler im Browser geprüft; Rückmeldungen der Tester stehen aus). **Ab 4.94 nur gebaut und kompiliert, nicht an Hardware geprüft:** Löschen des ESP32-Dateisystems (4.97), feste IP in der minimalen Firmware (4.95), git-Installation durch die Installationsskripte und die Frage beim Übersetzen (4.98, nicht an einem frischen PC oder Mac getestet) Alles ab 4.11 (Einstellungen sichern/übernehmen, Ausgabe und Abbrechen beim ESP32-Build, Verbinden beim Start, inkrementelles Speichern und seine Tastenkombination, Kopfbereich (Abstand in Issue 22 nicht bestätigt), Erweiterungen mit `symlink://`, Name und Beschreibung aus `libraries.json`) wurde nur gebaut und kompiliert, nicht auf Hardware oder im Browser getestet. IRremote 4.x für InfraredMLX ist nicht mit einem Pico geprüft. Die Übersetzungen der neuen Texte (CSV) sind ungeprüft. Die Menüs ab 4.51 sind vom Entwickler im Browser getestet (4.74: Rückmeldung „Funktioniert“); Dunkler Modus und Dateinamen mit Datum (4.44 bis 4.50) ebenfalls. **Ab 4.99 nur gebaut und kompiliert, nicht an Hardware oder im Browser geprüft:** die Änderungen von 5.04 bis 5.12 (Parameterformular, House-Formular, Name, Symbole, Niederländisch, Hilfe-Adressen); die Installationsskripte nur mit `bash -n`. Bitte besonders Aussehen und Bedienung des Parameterformulars und das Entfernen der alten Desktop-Symbole prüfen.

**Wiki:** Paket `webmobaledlib_Wiki_Gesamt_Stand_5.39.zip` (alle Seiten im Namensraum `mobaledlibstudio`, an die neuen Menüs angepasst, Hinweise in `LIESMICH_Wiki_Gesamt.md`). Die Bilder (Menüband, Programm Einstellungen, ARDUINO-IDE Einstellungen, Optionen, Datei-Menü, Verbinden) zeigen noch den alten Stand und müssen neu aufgenommen werden.

**Geplant:** Quell-URL direkt in der `platformio.ini` (Issue 6) ist nicht vorgesehen (Cache und `symlink://` bleiben); Rückfragen dazu stehen im Issue.

## Davor (3.66 bis 3.93)

Siehe RELEASE_Hinweise_3.93.md.
