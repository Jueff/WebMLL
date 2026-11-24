// MLLAdminCommunication.h - Administration und Identifikation ueber serielle Schnittstelle (nur ESP32 und Pico)
// Version 1.00 (2026-11-23): Neu: gemeinsame Empfangsroutine fuer die Protokolle MLLCFG und MLLIDENT (alle Zeilen beginnen mit '~'), Fehler als '~MLLERR <Grund>'
// Author: Jürgen Winkler
//
// Serielles Protokoll (alle Zeilen beginnen mit '~'):
//
// --- Konfiguration (MLLCFG) -----------------------------------------------------------
//   ~MLLCFG INFO                      -> ~MLLCFG INFO proto=2 sig=<Signatur> cfg=<CRC32 der Datei> valid=<0|1> free=<Bytes>
//   ~MLLCFG BEGIN <Laenge> <CRC32>    -> ~MLLCFG READY                      (CRC32 in Hex, ueber die ganze Datei)
//   ~MLLCFG DATA <Position> <Hex>     -> ~MLLCFG ACK <neue Position>
//   ~MLLCFG END                       -> ~MLLCFG OK  (danach Neustart)
//   ~MLLCFG ABORT                     -> ~MLLCFG OK
//   Fehler:                              ~MLLERR <Grund>
//
// --- Identifikation (MLLIDENT) --------------------------------------------------------
//   ~MLLIDENT 1   Blinken starten bzw. verlaengern (der PC schickt die Zeile jede Sekunde)  (keine Antwort)
//   ~MLLIDENT 0   Blinken beenden                                                         (keine Antwort)
// Kommt MLL_IDENT_TIMEOUT ms lang keine Zeile mehr (serielle Verbindung getrennt, Dialog geschlossen), endet das Blinken.
// Ein Neustart beendet es ebenfalls (der Zustand liegt nur im RAM).
//
// ---------------------------------------------------------------------------------------
// Beide Protokolle werden ueber eine gemeinsame Empfangsroutine verarbeitet:
//   MllAdminReceive(char c, Stream &port)  // fuer jedes empfangene Zeichen aufrufen (USB: Serial, WLAN: mllDeviceClient), Antworten gehen an port
//   Gibt true zurueck, wenn das Zeichen zu einer '~'-Zeile gehoert und verarbeitet wurde.

#ifndef __MLL_ADMIN_COMMUNICATION_H__
#define __MLL_ADMIN_COMMUNICATION_H__

#if defined(MLL_DYNAMIC_CONFIG) || defined(MLL_IDENTIFY)

#ifndef MLL_CFG_LINE_MAX
#define MLL_CFG_LINE_MAX     260
#endif

//----------------------------------------
static void MllCommunicationError(Stream &port, const __FlashStringHelper* Reason)
{
  port.print(F("~MLLERR "));
  port.println(Reason);
}

#include "MLLDynConfig.h"
#include "MLLIdentify.h"

#if !defined(MLL_DYNAMIC_CONFIG)
// Stub for MllCfgProcessLine when MLL_DYNAMIC_CONFIG is not defined
static void MllCfgProcessLine(Stream &port, char *Line)
{
  MllCommunicationError(port, F("MLLCFG not supported"));
}
#endif


//----------------------------------------
bool MllAdminReceive(char c, Stream &port)
//----------------------------------------
// Zentrale Empfangsroutine fuer alle Admin-Kommandos (Prefix '~').
// Wird fuer jedes empfangene Zeichen aufgerufen.
// Gibt true zurueck, wenn das Zeichen zu einer '~'-Zeile gehoert.
// Verarbeitet sowohl MLLCFG als auch MLLIDENT Kommandos.
{
  if (c != '~') return false;
  static char Line[MLL_CFG_LINE_MAX];
  size_t n = 0;
  bool Over = false, Complete = false;
  unsigned long Deadline = millis() + 1000;
  while (millis() < Deadline)
     {
     if (!port.available()) { delay(1); continue; }  // WLAN und Watchdog bedienen
     char x = port.read();
     Deadline = millis() + 1000;
     if (x == '\n') { Complete = true; break; }
     if (x == '\r') continue;
     if (n < sizeof(Line) - 1) Line[n++] = x;
     else Over = true;
     }
  Line[n] = 0;
  if (!Complete || Over)                      MllCommunicationError(port, F("line"));
  else if (strncmp(Line, "MLLCFG ", 7) == 0)  MllCfgProcessLine(port, Line + 7);
  else if (strncmp(Line, "MLLIDENT ", 9) == 0) MllIdentProcessLine(port, Line + 9);  // MLLIDENT wird in MllIdentProcessLine verarbeitet
  else                                        MllCommunicationError(port, F("cmd"));
  return true;
}

#endif // MLL_DYNAMIC_CONFIG || MLL_IDENTIFY

#endif // __MLL_ADMIN_COMMUNICATION_H__