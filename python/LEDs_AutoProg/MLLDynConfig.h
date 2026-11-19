// MLLDynConfig.h - Konfiguration getrennt vom Programm (nur ESP32 und Pico)
//
// Ist MLL_DYNAMIC_CONFIG gesetzt (der Programm Generator schreibt es in LEDs_AutoProg.h), dann stehen die Datentabellen
//   Config[], Ext_Addr[], Store_Values[] und LED2Var_Tab[]
// nicht im Programm. Sie liegen als eine Datei (/mllcfg.bin) im Dateisystem (LittleFS) und werden beim Start in den RAM geladen.
// Der Programm Generator uebertraegt die Datei ueber die serielle Schnittstelle. Das Programm selbst wird nur geladen, wenn sich
// der Quelltext oder die Struktur (LED Anzahl, Pins, Erweiterungen, ...) geaendert hat. Erkannt wird das mit MLL_FIRMWARE_SIG.
//
// Dateiformat (little endian):
//   0  "MLLC"
//   4  Version (2)
//   5  reserviert
//   6  Groesse von Config_RAM (u16)
//   8  Laenge Config (u32)
//  12  Laenge Ext_Addr (u32)
//  16  Laenge Store_Values (u32)
//  20  Laenge LED2Var_Tab (u32)
//  24  Laenge Startwerte (u32, Eintraege zu 3 Bytes: Kanal u16, Wert u8)
//  28  CRC32 ueber die Nutzdaten (u32)
//  32  Signatur der Firmware (16 Zeichen, MLL_FIRMWARE_SIG): die Datei wird nur geladen, wenn sie zu dieser Firmware gehoert
//  48  Nutzdaten: Config, Ext_Addr, Store_Values, LED2Var_Tab, Startwerte
//
// Serielles Protokoll (Zeilen, die mit '~' beginnen; Antworten ebenfalls):
//   ~MLLCFG INFO                      -> ~MLLCFG INFO proto=2 sig=<Signatur> cfg=<CRC32 der Datei> valid=<0|1> free=<Bytes>
//   ~MLLCFG BEGIN <Laenge> <CRC32>    -> ~MLLCFG READY                      (CRC32 in Hex, ueber die ganze Datei)
//   ~MLLCFG DATA <Position> <Hex>     -> ~MLLCFG ACK <neue Position>
//   ~MLLCFG END                       -> ~MLLCFG OK  (danach Neustart)
//   ~MLLCFG ABORT                     -> ~MLLCFG OK
//   Fehler:                              ~MLLCFG ERR <Grund>

#ifndef __MLL_DYN_CONFIG_H__
#define __MLL_DYN_CONFIG_H__

#if defined(MLL_DYNAMIC_CONFIG)

#include <LittleFS.h>

#ifndef MLL_FIRMWARE_SIG
  #define MLL_FIRMWARE_SIG "unknown"
#endif

#define MLL_CFG_PATH         "/mllcfg.bin"
#define MLL_CFG_TMP          "/mllcfg.tmp"
#define MLL_CFG_HEADER_SIZE  48
#define MLL_CFG_VERSION      2
#define MLL_CFG_SIG_LEN      16
#define MLL_CFG_PARTS        5
#define MLL_CFG_LINE_MAX     260

typedef struct
    {
    const uint8_t *config;   uint32_t configLen;
    const uint8_t *extAddr;  uint32_t extAddrLen;
    const uint8_t *store;    uint32_t storeLen;
    const uint8_t *l2v;      uint32_t l2vLen;
    const uint8_t *start;    uint32_t startLen;
    uint8_t       *ram;      uint16_t ramLen;
    uint32_t       id;       // CRC32 der geladenen Datei
    bool           valid;
    } MllDynConfig_T;

static MllDynConfig_T mllDyn;
static const uint8_t  mllEmptyConfig[] = { EndCfg };

MobaLedLib_C* pMobaLedLib;

// Bis zum Neustart gueltige Daten fuer die Tabellen (in der .ino ueber diese Makros benutzt)
#define MLL_EXT_ADDR_TAB      ((const Ext_Addr_T*)mllDyn.extAddr)
#define MLL_EXT_ADDR_SIZE     ((uint16_t)mllDyn.extAddrLen)
#define MLL_STORE_TAB         ((const uint8_t*)mllDyn.store)
#define MLL_STORE_SIZE        (mllDyn.storeLen)
#define MLL_L2V_TAB           ((const LED2Var_Tab_T*)mllDyn.l2v)
#define MLL_L2V_COUNT         (mllDyn.l2vLen / sizeof(LED2Var_Tab_T))

//-----------------------------------------------------------------
static uint32_t MllCrc32(uint32_t crc, const uint8_t *data, size_t len)
//-----------------------------------------------------------------
{
  crc = ~crc;
  while (len--)
     {
     crc ^= *data++;
     for (uint8_t k = 0; k < 8; k++) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
     }
  return ~crc;
}

//--------------------------
static bool MllFsBegin()
//--------------------------
{
  static bool Done = false, Ok = false;
  if (!Done)
     {
     Done = true;
     #ifdef ESP32
       Ok = LittleFS.begin(true);       // true: formatieren, wenn noch kein Dateisystem da ist
     #else
       Ok = LittleFS.begin();           // Pico: die Groesse steht in platformio.ini (board_build.filesystem_size)
     #endif
     }
  return Ok;
}

//---------------------------------
static size_t MllFsFreeBytes()
//---------------------------------
{
  #ifdef ESP32
    return LittleFS.totalBytes() - LittleFS.usedBytes();
  #else
    FSInfo fi;
    if (!LittleFS.info(fi)) return 0;
    return fi.totalBytes - fi.usedBytes;
  #endif
}

//-------------------------------------------------------------
static bool MllCfgParseHeader(const uint8_t *h, size_t fileSize, uint32_t *len /*[MLL_CFG_PARTS]*/, uint16_t *ramLen, uint32_t *crc)
//-------------------------------------------------------------
// Prueft Kennung, Version, Laengen und vor allem die Signatur: Eine Datei, die fuer eine andere Firmware erzeugt wurde, wird nie benutzt.
{
  if (fileSize < MLL_CFG_HEADER_SIZE) return false;
  if (memcmp(h, "MLLC", 4) != 0 || h[4] != MLL_CFG_VERSION) return false;
  if (strlen(MLL_FIRMWARE_SIG) != MLL_CFG_SIG_LEN || memcmp(h + 32, MLL_FIRMWARE_SIG, MLL_CFG_SIG_LEN) != 0) return false;
  memcpy(ramLen, h + 6, 2);
  memcpy(len,    h + 8, 4 * MLL_CFG_PARTS);
  memcpy(crc,    h + 28, 4);
  uint64_t Sum = 0;
  for (uint8_t i = 0; i < MLL_CFG_PARTS; i++) Sum += len[i];
  return Sum + MLL_CFG_HEADER_SIZE == fileSize;
}

//-------------------------
static bool MllDynLoad()
//-------------------------
// Laedt /mllcfg.bin in den RAM. Ohne gueltige Datei bleibt die Konfiguration leer (die LEDs bleiben dunkel),
// das Programm laeuft aber und kann ueber die serielle Schnittstelle eine neue Konfiguration bekommen.
{
  memset(&mllDyn, 0, sizeof(mllDyn));
  mllDyn.config    = mllEmptyConfig;
  mllDyn.configLen = sizeof(mllEmptyConfig);
  if (!MllFsBegin()) return false;
  File f = LittleFS.open(MLL_CFG_PATH, "r");
  if (!f) return false;
  size_t Size = f.size();
  uint8_t *Buf = Size >= MLL_CFG_HEADER_SIZE ? (uint8_t*)malloc(Size) : NULL;
  bool Ok = Buf != NULL && f.read(Buf, Size) == (int)Size;
  f.close();
  uint32_t Len[MLL_CFG_PARTS], Crc;
  uint16_t RamLen;
  if (Ok) Ok = MllCfgParseHeader(Buf, Size, Len, &RamLen, &Crc) && MllCrc32(0, Buf + MLL_CFG_HEADER_SIZE, Size - MLL_CFG_HEADER_SIZE) == Crc;
  uint8_t *Ram = NULL;
  if (Ok)
     {
     Ram = (uint8_t*)calloc(RamLen ? RamLen : 1, 1);
     Ok  = Ram != NULL;
     }
  if (!Ok)
     {
     free(Buf);
     free(Ram);
     return false;
     }
  const uint8_t *p = Buf + MLL_CFG_HEADER_SIZE;
  mllDyn.config   = p; mllDyn.configLen  = Len[0]; p += Len[0];
  mllDyn.extAddr  = p; mllDyn.extAddrLen = Len[1]; p += Len[1];
  mllDyn.store    = p; mllDyn.storeLen   = Len[2]; p += Len[2];
  mllDyn.l2v      = p; mllDyn.l2vLen     = Len[3]; p += Len[3];
  mllDyn.start    = p; mllDyn.startLen   = Len[4];
  mllDyn.ram      = Ram;
  mllDyn.ramLen   = RamLen;
  mllDyn.id       = MllCrc32(0, Buf, Size);
  mllDyn.valid    = true;
  return true;
}

//-----------------------------------------------------------------
static void MllDynSetStartValues(MobaLedLib_C &MobaLedLib)
//-----------------------------------------------------------------
// Ersatz fuer Set_Start_Values(): die Startwerte der Eingangskanaele stehen in der Konfigurationsdatei
{
  for (uint32_t i = 0; i + 3 <= mllDyn.startLen; i += 3)
     {
     uint16_t Channel;
     memcpy(&Channel, mllDyn.start + i, 2);
     MobaLedLib.Set_Input(Channel, mllDyn.start[i + 2]);
     }
}

// ---- Empfang einer neuen Konfiguration ----------------------------------------------------------
static File     mllRxFile;
static bool     mllRxActive = false;
static uint32_t mllRxSize, mllRxPos, mllRxCrcExp, mllRxCrc;
static uint8_t  mllRxHead[MLL_CFG_HEADER_SIZE];

//----------------------------------------
static void MllRxAbort()
//----------------------------------------
{
  if (mllRxActive)
     {
     mllRxFile.close();
     mllRxActive = false;
     }
  if (MllFsBegin()) LittleFS.remove(MLL_CFG_TMP);
}

//----------------------------------------
static void MllCfgErr(const __FlashStringHelper *Reason)
//----------------------------------------
{
  Serial.print(F("~MLLCFG ERR "));
  Serial.println(Reason);
}

//---------------------------------------
static int MllHexVal(char c)
//---------------------------------------
{
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return -1;
}

//------------------------------------------
static void MllRestart()
//------------------------------------------
{
  Serial.flush();
  delay(300);
  #ifdef ESP32
    ESP.restart();
  #else
    rp2040.restart();
  #endif
}

//-------------------------------------------
static void MllCfgProcessLine(char *Line)
//-------------------------------------------
{
  if (strcmp(Line, "INFO") == 0)
     {
     char s[120];
     sprintf(s, "~MLLCFG INFO proto=2 sig=%s cfg=%08lx valid=%d free=%lu", MLL_FIRMWARE_SIG, (unsigned long)mllDyn.id, mllDyn.valid ? 1 : 0, (unsigned long)(MllFsBegin() ? MllFsFreeBytes() : 0));
     Serial.println(s);
     }
  else if (strncmp(Line, "BEGIN ", 6) == 0)
     {
     MllRxAbort();
     char *End;
     uint32_t Size = strtoul(Line + 6, &End, 10);
     uint32_t Crc  = strtoul(End, NULL, 16);
     if (Size < MLL_CFG_HEADER_SIZE)                  { MllCfgErr(F("size"));  return; }
     if (!MllFsBegin())                               { MllCfgErr(F("fs"));    return; }
     if (Size + 4096 > MllFsFreeBytes())              { MllCfgErr(F("full"));  return; }
     mllRxFile = LittleFS.open(MLL_CFG_TMP, "w");
     if (!mllRxFile)                                  { MllCfgErr(F("open"));  return; }
     mllRxActive = true;
     mllRxSize = Size; mllRxCrcExp = Crc; mllRxPos = 0; mllRxCrc = 0;
     Serial.println(F("~MLLCFG READY"));
     }
  else if (strncmp(Line, "DATA ", 5) == 0)
     {
     if (!mllRxActive)                                { MllCfgErr(F("nobegin")); return; }
     char *End;
     uint32_t Pos = strtoul(Line + 5, &End, 10);
     if (Pos != mllRxPos)                             { MllCfgErr(F("pos"));   return; }
     while (*End == ' ') End++;
     size_t Len = strlen(End);
     uint8_t Buf[MLL_CFG_LINE_MAX / 2];
     if ((Len & 1) || Len / 2 > sizeof(Buf) || mllRxPos + Len / 2 > mllRxSize) { MllCfgErr(F("len")); return; }
     for (size_t i = 0; i < Len; i += 2)
        {
        int h = MllHexVal(End[i]), l = MllHexVal(End[i + 1]);
        if (h < 0 || l < 0)                           { MllCfgErr(F("hex"));   return; }
        Buf[i / 2] = (uint8_t)(h << 4 | l);
        }
     size_t n = Len / 2;
     if (mllRxFile.write(Buf, n) != n)
        {
        MllRxAbort();
        MllCfgErr(F("write"));
        return;
        }
     for (size_t i = 0; i < n && mllRxPos + i < MLL_CFG_HEADER_SIZE; i++) mllRxHead[mllRxPos + i] = Buf[i];
     mllRxCrc = MllCrc32(mllRxCrc, Buf, n);
     mllRxPos += n;
     Serial.print(F("~MLLCFG ACK "));
     Serial.println(mllRxPos);
     }
  else if (strcmp(Line, "END") == 0)
     {
     if (!mllRxActive)                                { MllCfgErr(F("nobegin")); return; }
     mllRxFile.close();
     mllRxActive = false;
     uint32_t Len[MLL_CFG_PARTS], Crc;
     uint16_t RamLen;
     bool Ok = mllRxPos == mllRxSize && mllRxCrc == mllRxCrcExp && MllCfgParseHeader(mllRxHead, mllRxSize, Len, &RamLen, &Crc);
     if (!Ok)
        {
        MllRxAbort();
        MllCfgErr(F("check"));
        return;
        }
     LittleFS.remove(MLL_CFG_PATH);
     if (!LittleFS.rename(MLL_CFG_TMP, MLL_CFG_PATH))   { LittleFS.remove(MLL_CFG_TMP); MllCfgErr(F("rename")); return; }
     Serial.println(F("~MLLCFG OK"));
     MllRestart();
     }
  else if (strcmp(Line, "ABORT") == 0)
     {
     MllRxAbort();
     Serial.println(F("~MLLCFG OK"));
     }
  else MllCfgErr(F("cmd"));
}

//-----------------------------------
static bool MllCfgReceive(char c)
//-----------------------------------
// Wird fuer jedes empfangene Zeichen aufgerufen. Zeilen, die mit '~' beginnen, werden hier vollstaendig gelesen
// und ausgefuehrt (dauert bei 115200 Baud etwa 20 ms). Gibt true zurueck, wenn das Zeichen verbraucht wurde.
{
  if (c != '~') return false;
  static char Line[MLL_CFG_LINE_MAX];
  size_t n = 0;
  bool Over = false, Complete = false;
  unsigned long Deadline = millis() + 1000;
  while (millis() < Deadline)
     {
     if (!Serial.available()) continue;
     char x = Serial.read();
     Deadline = millis() + 1000;
     if (x == '\n') { Complete = true; break; }
     if (x == '\r') continue;
     if (n < sizeof(Line) - 1) Line[n++] = x;
     else Over = true;
     }
  Line[n] = 0;
  if (!Complete || Over)                      MllCfgErr(F("line"));
  else if (strncmp(Line, "MLLCFG ", 7) == 0)  MllCfgProcessLine(Line + 7);
  else                                        MllCfgErr(F("cmd"));
  return true;
}

#endif // MLL_DYNAMIC_CONFIG
#endif // __MLL_DYN_CONFIG_H__
