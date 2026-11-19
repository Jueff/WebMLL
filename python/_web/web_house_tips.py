# Datei-Version: 1.00 (2026-11-19) - web_house_tips.py
# ----------------------------------------------------------------------------------------------
# Name:           web_house_tips.py
# Path:           _web/web_house_tips.py
# Version:        1.00
# Last Update:    2026-11-19
# Author:         Harold Linke
# Licence:        LGPL V2.1
# History of Change:
#   1.00  2026-11-19  Neu: Tooltips der Raumeffekte (House, GasLights) und der Felder des Dialogs, aus dem Formular UserForm_House des Excel-Programms
#                     (ControlTipText). Die Texte sind die deutschen Schluessel der Tabelle Languages (csv/Languages.csv); die Uebersetzung holt
#                     web_form_house.py mit M09.Get_Language_Str.
# ----------------------------------------------------------------------------------------------
"""Tooltips des Dialogs "House" / "GasLights" (deutsche Originaltexte aus dem Excel-Programm, Schluessel der Tabelle Languages)."""

# Name des Knopfes (wie in Userform_House.house_button_list_str) -> Tooltip
BUTTON_TIPS = {
    'ROOM_DARK': 'Raum mit dunkler Beleuchtung',
    'ROOM_BRIGHT': 'Raum mit heller Beleuchtung',
    'ROOM_WARM_W': 'Raum mit warm weißer Beleuchtung',
    'ROOM_RED': 'Raum mit roter Beleuchtung',
    'ROOM_D_RED': 'Raum mit dunkler roter Beleuchtung',
    'ROOM_COL0': 'Raum welcher mit der Benutzerdefinierten Farbe 0 beleuchtet wird',
    'ROOM_COL1': 'Raum welcher mit der Benutzerdefinierten Farbe 1 beleuchtet wird',
    'ROOM_COL2': 'Raum welcher mit der Benutzerdefinierten Farbe 2 beleuchtet wird',
    'ROOM_COL3': 'Raum welcher mit der Benutzerdefinierten Farbe 3 beleuchtet wird',
    'ROOM_COL4': 'Raum welcher mit der Benutzerdefinierten Farbe 4 beleuchtet wird',
    'ROOM_COL5': 'Raum welcher mit der Benutzerdefinierten Farbe 5 beleuchtet wird',
    'ROOM_COL345': 'Raum welcher zufällig mit der Benutzerdefinierten Farbe 3, 4 oder 5  beleuchtet wird',
    'FIRE': 'Simulation eines Feuers',
    'FIRED': 'Simulation eines dunklen Feuers',
    'FIREB': 'Simulation eines hellen Feuers',
    'ROOM_CHIMNEY': 'Raum mit offenem Kamin oder normalem Licht',
    'ROOM_CHIMNEYD': 'Raum mit dunklem offenem Kamin oder normalem Licht',
    'ROOM_CHIMNEYB': 'Raum mit hellem offenem Kamin oder normalem Licht',
    'ROOM_TV0': 'Raum in dem das TV-Programm 0 läuft oder ein normales Licht brennt',
    'ROOM_TV0_CHIMNEY': 'Raum in dem das TV-Programm 0 läuft, ein offener Kamin oder ein normales Licht brennt',
    'ROOM_TV0_CHIMNEYD': 'Raum in dem das TV-Programm 0 läuft, ein offener Kamin oder ein normales Licht brennt (Dunkler)',
    'ROOM_TV0_CHIMNEYB': 'Raum in dem das TV-Programm 0 läuft, ein offener Kamin oder ein normales Licht brennt (Heller)',
    'ROOM_TV1': 'Raum in dem das TV-Programm 1 läuft oder ein normales Licht brennt',
    'ROOM_TV1_CHIMNEY': 'Raum in dem das TV-Programm 1 läuft, ein offener Kamin oder ein normales Licht brennt',
    'ROOM_TV1_CHIMNEYD': 'Raum in dem das TV-Programm 1 läuft, ein offener Kamin oder ein normales Licht brennt (Dunkler)',
    'ROOM_TV1_CHIMNEYB': 'Raum in dem das TV-Programm 1 läuft, ein offener Kamin oder ein normales Licht brennt (Heller)',
    'NEON_LIGHT': 'Raum mit Neon Licht simuliert über eine RGB LED',
    'NEON_LIGHT1': 'Raum mit Neon Licht simuliert über eine einzelne LED an Kanal 1 (R)',
    'NEON_LIGHT2': 'Raum mit Neon Licht simuliert über eine einzelne LED an Kanal 2 (G)',
    'NEON_LIGHT3': 'Raum mit Neon Licht simuliert über eine einzelne LED an Kanal 3 (B)',
    'NEON_LIGHTD': 'Raum mit dunklem Neon Licht simuliert über eine RGB LED',
    'NEON_LIGHT1D': 'Raum mit dunklem Neon Licht simuliert über eine einzelne LED an Kanal 1 (R)',
    'NEON_LIGHT2D': 'Raum mit dunklem Neon Licht simuliert über eine einzelne LED an Kanal 2 (G)',
    'NEON_LIGHT3D': 'Raum mit dunklem Neon Licht simuliert über eine einzelne LED an Kanal 3 (B)',
    'NEON_LIGHT3M': 'Raum mit mittel hellem Neon Licht simuliert über eine einzelne LED an Kanal 3 (B)',
    'NEON_LIGHTM': 'Raum mit mittel hellem Neon Licht simuliert über eine RGB LED',
    'NEON_LIGHT1M': 'Raum mit mittel hellem Neon Licht simuliert über eine einzelne LED an Kanal 1 (R)',
    'NEON_LIGHT2M': 'Raum mit mittel hellem Neon Licht simuliert über eine einzelne LED an Kanal 2 (G)',
    'NEON_LIGHT3L': 'Raum mit mehreren simulierten Neon Lichtern generiert über eine einzelne LED an Kanal 3 (B)',
    'NEON_LIGHTL': 'Raum mit mehreren simulierten Neon Lichtern generiert über eine RGB LED ',
    'NEON_LIGHT1L': 'Raum mit mehreren simulierten Neon Lichtern generiert über eine einzelne LED an Kanal 1 (R)',
    'NEON_LIGHT2L': 'Raum mit mehreren simulierten Neon Lichtern generiert über eine einzelne LED an Kanal 2 (G)',
    'SINGLE_LED1': 'Einzelne LED welche an Kanal 1 (R) eines WS2811 Moduls angeschlossen ist',
    'SINGLE_LED2': 'Einzelne LED welche an Kanal 2 (G) eines WS2811 Moduls angeschlossen ist',
    'SINGLE_LED3': 'Einzelne LED welche an Kanal 3 (B) eines WS2811 Moduls angeschlossen ist',
    'GAS_LIGHT3D': 'Langsam heller werdendes dunkles Gaslicht simuliert über eine einzelne LED an Kanal 3 (B)',
    'GAS_LIGHT1': 'Langsam heller werdendes Gaslicht simuliert über eine einzelne LED an Kanal 1 (R)',
    'GAS_LIGHT': 'Langsam heller werdendes Gaslicht simuliert über eine RGB LED',
    'GAS_LIGHT2': 'Langsam heller werdendes Gaslicht simuliert über eine einzelne LED an Kanal 2 (G)',
    'GAS_LIGHT3': 'Langsam heller werdendes Gaslicht simuliert über eine einzelne LED an Kanal 3 (B)',
    'GAS_LIGHTD': 'Langsam heller werdendes dunkles Gaslicht simuliert über eine RGB LED',
    'GAS_LIGHT1D': 'Langsam heller werdendes dunkles Gaslicht simuliert über eine einzelne LED an Kanal 1 (R)',
    'GAS_LIGHT2D': 'Langsam heller werdendes dunkles Gaslicht simuliert über eine einzelne LED an Kanal 2 (G)',
    'SKIP_ROOM': 'Dieser Raum wird nicht von der House() Funktion gesteuert. Er kann von Experten mit einer vorgeschalteten anderen Funktion aktiviert werden. ',
    'SINGLE_LED1D': 'Einzelne dunkle LED welche an Kanal 1 (R) eines WS2811 Moduls angeschlossen ist',
    'SINGLE_LED2D': 'Einzelne dunkle LED welche an Kanal 2 (G) eines WS2811 Moduls angeschlossen ist',
    'SINGLE_LED3D': 'Einzelne dunkle LED welche an Kanal 3 (B) eines WS2811 Moduls angeschlossen ist',
    'NEON_DEF_D': 'Defekte Neonröhre (simuliert über eine RGB LED)',
    'NEON_DEF3D': 'Defekte Neonröhre (simuliert über eine einzelne LED welche vom blauen Kanal eines WS2811 Moduls angesteuert wird)',
    'NEON_DEF1D': 'Defekte Neonröhre (simuliert über eine einzelne LED welche vom roten Kanal eines WS2811 Moduls angesteuert wird)',
    'NEON_DEF2D': 'Defekte Neonröhre (simuliert über eine einzelne LED welche vom grünen Kanal eines WS2811 Moduls angesteuert wird)',
    'CANDLE': 'Flackernde Kerze (simuliert über eine RGB LED)',
    'CANDLE1': 'Flackernde Kerze (simuliert über eine einzelne LED welche vom roten Kanal eines WS2811 Moduls angesteuert wird)',
    'CANDLE2': 'Flackernde Kerze (simuliert über eine einzelne LED welche vom grünen Kanal eines WS2811 Moduls angesteuert wird)',
    'CANDLE3': 'Flackernde Kerze (simuliert über eine einzelne LED welche vom blauen Kanal eines WS2811 Moduls angesteuert wird)',
}

# Feld des Dialogs -> Tooltip
FIELD_TIPS = {
    'min_cnt': 'Der Parameter beschreibt wie viele Räume mindestens beleuchtet sein sollen. Nach dem Einschalten werden nach einer zufälligen Zeit so lange zufällige Lichter eingeschaltet bis die vorgegebene Anzahl erreicht ist.',
    'max_cnt': 'Der Parameter bestimmt wie viele Räume gleichzeitig benutzt sein können. Wenn die Zahle erreicht ist werden LEDs zufällig abgeschaltet. Ist die Zahl größer als die Anzahl der LEDs, dann sind nach einiger Zeit alle LEDs an.',
    'on_limit': 'Der Parameter "On_Limit" bestimmt wie viele Räume gleichzeitig benutzt sein sollen. Wenn entsprechend viele LEDs an sind wird zum nächsten, zufällig gewählten, Zeitpunkt eine Lampe ausgeschaltet. Wenn dieser Parameter größer als die Anzahl der Räume ist, dann sind nach einiger Zeit alle Lichter an (Das entspricht unserem Zuhause).',
    'indiv': 'Wenn dieser Schalter aktiviert ist, dann können individuelle Zeiten verwendet werden. Ansonsten werden globale Konstanten benutzt (HOUSE_MIN_T=50, HOUSE_MAX_T=150). ',
    'min_time': 'Der Parameter "Min_T" beschreibt wie lange minimal gewartet wird bis eine Änderung der aktiven der Beleuchtungen erfolgt. Das Programm wählt einen zufälligen Zeitpunkt zwischen "Min_T" und "Max_T". Die Zeit kann zwischen 0 und 254 Sekunden liegen.',
    'max_time': 'Der Parameter "Max_T" beschreibt wie lange maximal gewartet wird bis eine Änderung der aktiven der Beleuchtungen erfolgt. Das Programm wählt einen zufälligen Zeitpunkt zwischen "Min_T" und "Max_T". Die Zeit kann zwischen 0 und 254 Sekunden liegen.',
    'inv': 'Mit diesem Schalter wird der Eingang der House Funktion Invertiert. Das kann z.B. zusammen mit der Schedule Funktion genutzt werden.',
    'led_channel': 'Gibt den verwendeten LED-Kanal an. Es können 4 verschiedene LED-Stränge angesteuert werden. 0 = Normal, 1 = Knopf Druck Aktion, 2, 3 Frei verfügbar.',
}
