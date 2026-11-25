Startprogramme fuer die Startseite von MobaLedLib Studio (Version 5.23)
=====================================================================

Hier liegen die Programme, die der Knopf "Anfangen" der Startseite in die Tabelle der gewaehlten Zentrale laedt.
Die Dateien sind MLL_pgf-Dateien (Programm Generator: Datei -> PGF-Datei speichern).

Namen (ohne Leerzeichen, genau so geschrieben):

  <Lichtmaschine>_<Zentrale>.MLL_pgf    zum Beispiel  Pico_Zero_MoLLi_Selectrix.MLL_pgf
  <Lichtmaschine>.MLL_pgf               zum Beispiel  Pico_Zero_MoLLi.MLL_pgf

Das Programm sucht zuerst die Datei fuer die Kombination, dann die Datei der Lichtmaschine allein.
Gibt es keine, wird die leere Tabelle der Zentrale geoeffnet und die Startseite weist darauf hin.

Lichtmaschine (Teil des Namens):
  Classic_Mini        Lichtmaschine Classic / Mini (Arduino Nano)
  Pro                 Lichtmaschine Pro (ESP32)
  Pico_Zero_MoLLi     Lichtmaschine Pico Zero / MoLLi (Raspberry Pi Pico)

Zentrale (Teil des Namens, nur fuer die Datei der Kombination):
  DCC, Selectrix, LNet, CAN     ("Ohne Zentrale" benutzt die Tabelle DCC, also DCC)

Die Datei wird in die aktive Tabelle der Zentrale geladen (wie "PGF-Datei lesen" mit Ziel aktive Tabelle).
