Datei-Version: 1.00 (2026-11-19) - DATEIEN_IM_PAKET_Issue26.md
Gilt für webMobaLedLib 4.25

# Issue 26: Welche Dateien müssen nicht ins Paket?

Grundlage ist die Liste von Jürgen und die Prüfung gegen den Code (Stand 4.25). Die Prüfung ist nach den Zugriffen im Python-Code gemacht, nicht durch Ausprobieren. Der Stand des Repos ist der vom 14.11., die Dateinamen stammen daraus.

## A. Unbedenklich entfernen (vom Programm erzeugt oder Reste, nichts im Code liest sie aus dem Paket)

| Datei | Befund |
|---|---|
| `LEDs_AutoProg/Start_AM328_Sub.cmd`, `Start_PICO_Sub.cmd`, `Start_ESP32_Sub.cmd` | werden bei jedem Übertragen neu geschrieben (`M08_ARDUINO.py`: `'Start_' + BoardName + '_Sub.cmd'`, `Create_Start_ESP32_Sub`) |
| `LEDs_AutoProg/Start_Arduino.cmd` | wird erzeugt (`M08_ARDUINO.py`, `Prog_Generator.py`) |
| `LEDs_AutoProg/*.cmd.1` | Sicherungskopien, nichts liest sie |
| `LEDs_AutoProg/MobaLedTest_config.json` | die Konfiguration liegt im Datenordner (`%APPDATA%\webMobaLedLib`), die Datei hier liest webMobaLedLib nicht |
| `LEDs_AutoProg/LEDs_AutoProg.h` | wird bei jeder Erzeugung von `M06_Write_Header.py` neu geschrieben; die minimale Firmware (ESP32 OTA) bringt ihre eigene mit |
| `Configuration/Configuration.cpp.d`, `.cpp.o`, `Configuration.elf`, `*.bin` | Ergebnisse des Simulators (`M39_Simulator.py` erzeugt sie bei Bedarf) |
| `Configuration/x64/Finished.txt` | nur als Konstante `FINISH_FILE` vorhanden, nichts liest sie |
| `LEDs_AutoConfig/*.txt`, `LEDs_AutoConfig/*.dl.*`, `LEDs_AutoProg_20250517_big1.h`, `cpip.css` | keine Zugriffe im Code (Testreste). Der Ordner `LEDs_AutoConfig` selbst bleibt, das Programm schreibt dort |
| `platformio.ini.ota` | keine Zugriffe im Code |
| `hex-files/_old`, `hex-files_test` | keine Zugriffe im Code |

## B. Bleibt (wird gebraucht)

| Datei | Grund |
|---|---|
| `LEDs_AutoProg/fastBuild.cmd`, `fastBuild2.cmd` | werden **nicht** erzeugt; die erzeugten `Start_*_Sub.cmd` rufen sie auf (Weg über die ARDUINO IDE) |
| `LEDs_AutoProg/boards.local.txt` | wird für die ARDUINO IDE kopiert (`M08_Fast_ARDUINO.py`); weg, sobald der Weg über die ARDUINO IDE nicht mehr unterstützt wird |
| `LEDs_AutoProg/*.ino`, `*.h` (außer `LEDs_AutoProg.h`), `*.cpp` | Quellcode der Firmware |
| `Configuration/Configuration.cpp`, `build.cmd`, `x64`, `x86` (DLL) | Windows-Weg für die LED-Konfiguration (`CfgName_LED`, `CfgBuild_Script`) |
| `csv/Prog_Generator_MobaLedLib.xlsm` | zurzeit der Master (siehe deine Antwort im Issue) |
| `hex-files/*.hex`, `*.blthex`, `*.cmd`, `Pico_WH_mDNS` | Programmieren der Tiny- und Pico-Module (`UserForm_Options.py` greift auf `hex-files/Pico_WH_mDNS` zu) |
| `Restart_ProgGen.cmd`, `Update_Libraries.cmd` (Hauptordner) | `M37_Inst_Libraries.py` ruft sie auf (Excel-Weg) |

## C. Unklar, bitte entscheiden

| Datei | Befund |
|---|---|
| `python/csv/Update_Libraries.cmd` | zweite Kopie neben der im Hauptordner; `M37` benutzt `GetWorkbookPath() + '/Update_Libraries.cmd'`, das ist die im Hauptordner. Die in `csv` wirkt überflüssig, aber ich habe es nicht durch Ausprobieren bestätigt. |
| `python/platformio.ini` (im Hauptordner) | wird beim Übertragen neu geschrieben (`M08_ARDUINO.py` schreibt `..//platformio.ini`) und ist deshalb für Update und Prüfung bereits „flüchtig“. Kann weg. Das Programm legt sie an. Bitte einmal mit einer frischen Installation prüfen. |
| `hex-files/Read_me.txt`, `iprtinymain.c`, `Set_Fuses.cmd`, `upload_hex.cmd` | im Python-Code nicht verwendet, gehören aber zu den Hex-Dateien für die Tiny-Module (Handarbeit). Ich würde sie als Hilfe für Selbstbauer lassen. |

## Auswirkung auf Update und Prüfung

- Das Release wird aus dem Ordnerinhalt gebaut. Die Prüfliste (`release_manifest.json`) folgt automatisch, es muss nichts angepasst werden.
- Ein **Update** auf das neue Release löscht die entfernten Dateien auf den Rechnern der Anwender, außer den „flüchtigen“ Pfaden (`LEDs_AutoProg/LEDs_AutoProg.h`, `LEDs_AutoProg/*.cmd`, `platformio.ini`). Werden mehr als 20 Dateien gelöscht, fragt das Programm vor dem Update ausdrücklich nach (Hinweis in der Update-Anzeige). Das ist hier der Fall: Der Anwender sieht die Rückfrage und bestätigt sie.
- Update, Prüfung und Reparatur behandeln die Ordner `LEDs_AutoProg`, `LEDs_AutoConfig`, `Configuration` und `processed_output` schon jetzt als „vom Programm beschrieben“: fehlende Vorlagen werden gemeldet, abweichende Inhalte nicht.

## Vorschlag zum Vorgehen

1. Die Dateien aus A im Repo löschen.
2. Mit einer **frischen Installation** (Release-ZIP entpacken, kein altes Verzeichnis) „Setup übertragen“ und „Setup simulieren“ ausprobieren (Windows und, wenn möglich, Pi).
3. Danach die Punkte aus C entscheiden.
