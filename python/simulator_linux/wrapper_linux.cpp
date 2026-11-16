// MobaLedLibWrapper fuer Linux (ohne Fenster)
// Datei-Version: 1.00 (2026-11-15) - wrapper_linux.cpp
// Abgeleitet von Wrapper.cpp (Copyright (C) 2022 Juergen Winkler, LGPL 2.1 oder neuer).
// Die Simulation ist unveraendert; das Win32-Fenster entfaellt, die LED-Farben holt der
// Aufrufer ueber GetLedColor/GetLedColors und zeichnet sie selbst.
#include <MobaLedLib.h>
#include <mutex>
#include <cstring>
#include <cstdlib>

#define EXPORT extern "C" __attribute__((visibility("default")))
#define NUM_LEDS 256
#define T_EQUAL_THEN     0
#define T_NOT_EQUAL_THEN 1
#define T_LESS_THEN      2
#define T_GREATER_THAN   3
#define T_BIN_MASK       4
#define T_NOT_BIN_MASK   5

typedef struct __attribute__((__packed__)) {
    uint8_t Var_Nr;
    uint8_t LED_Nr;
    uint8_t Offset_and_Typ;
    uint8_t Val;
} LED2Var_Tab_T;

static CRGB* pLeds = new CRGB[NUM_LEDS];
static unsigned char* l2vConfig = NULL;
static int l2vConfigLength = 0;
static uint8_t MyConfigRam[2048];
static std::recursive_mutex lock_;
static bool windowOpen = false;

MobaLedLib_Prepare();

MobaLedLib_Configuration()
{
    RGB_Heartbeat(0)
    RGB_Heartbeat(1)
    ConstRGB(8, SI_1, 0, 0, 0, 127, 127, 127)
    EndCfg
};

static void Update_LED2Var()
{
    if (l2vConfig == NULL) return;
    for (uint8_t i = 0; i < l2vConfigLength / sizeof(LED2Var_Tab_T); i++)
    {
        const LED2Var_Tab_T* p = (LED2Var_Tab_T*)(l2vConfig + i * sizeof(LED2Var_Tab_T));
        uint8_t Var_Nr = p->Var_Nr;
        uint8_t LED_Nr = p->LED_Nr;
        uint8_t Offset_and_Typ = p->Offset_and_Typ;
        uint8_t Val = p->Val;
        uint8_t Offset = Offset_and_Typ >> 3;
        int8_t  Typ = Offset_and_Typ & 0x07;
        uint8_t LED_Val = *(&pLeds[LED_Nr].r + Offset);
        uint8_t Res;
        switch (Typ)
        {
        case T_GREATER_THAN:   Res = (LED_Val > Val); break;
        case T_LESS_THEN:      Res = (LED_Val < Val); break;
        default:
        case T_EQUAL_THEN:     Res = (LED_Val == Val); break;
        case T_NOT_EQUAL_THEN: Res = (LED_Val != Val); break;
        case T_BIN_MASK:       Res = (LED_Val & Val); break;
        case T_NOT_BIN_MASK:   Res = !(LED_Val & Val); break;
        }
        if (pMobaLedLib != NULL) pMobaLedLib->Set_Input(Var_Nr, Res);
    }
}

EXPORT int GetWrapperVersion() { return 10100; }   // gleiche Schnittstelle wie die Windows-DLL (1.01.00)

EXPORT const unsigned char* CreateSampleConfig()
{
    std::lock_guard<std::recursive_mutex> g(lock_);
    memset(pLeds, 0, NUM_LEDS * sizeof(CRGB));
    if (pMobaLedLib != NULL) delete pMobaLedLib;
    pMobaLedLib = new MobaLedLib_C(pLeds, NUM_LEDS, Config, MyConfigRam, sizeof(MyConfigRam), NULL, NULL);
    return &pLeds[0].r;
}

EXPORT const unsigned char* CreateEx(unsigned char* config, int configLenght, unsigned char* led2var, int led2varLength)
{
    std::lock_guard<std::recursive_mutex> g(lock_);
    memset(pLeds, 0, NUM_LEDS * sizeof(CRGB));
    void* myConfig = malloc(configLenght);
    memcpy(myConfig, config, configLenght);
    free(l2vConfig);
    l2vConfig = (unsigned char*)malloc(led2varLength > 0 ? led2varLength : 1);
    if (led2var != NULL && led2varLength > 0) memcpy(l2vConfig, led2var, led2varLength);
    l2vConfigLength = led2varLength;
    if (pMobaLedLib != NULL) delete pMobaLedLib;
    pMobaLedLib = new MobaLedLib_C(pLeds, NUM_LEDS, (unsigned char*)myConfig, MyConfigRam, sizeof(MyConfigRam), NULL, NULL);
    return &pLeds[0].r;
}

EXPORT const unsigned char* Create(unsigned char* config, int configLenght) { return CreateEx(config, configLenght, NULL, 0); }

EXPORT void Update()
{
    std::lock_guard<std::recursive_mutex> g(lock_);
    if (pMobaLedLib != NULL) pMobaLedLib->Update();
    Update_LED2Var();
}

EXPORT int GetLedColor(unsigned char ledNr)
{
    if (pMobaLedLib == NULL) return 0;
    return pLeds[ledNr].r + (pLeds[ledNr].g << 8) + (pLeds[ledNr].b << 16);
}

// neu: Farben von count LEDs ab first als RGB-Tripel in buf (3*count Bytes); liefert die Anzahl
EXPORT int GetLedColors(unsigned char first, int count, unsigned char* buf)
{
    std::lock_guard<std::recursive_mutex> g(lock_);
    if (pMobaLedLib == NULL || buf == NULL) return 0;
    int n = 0;
    for (int i = 0; i < count && first + i < NUM_LEDS; i++, n++)
    {
        buf[3 * i] = pLeds[first + i].r; buf[3 * i + 1] = pLeds[first + i].g; buf[3 * i + 2] = pLeds[first + i].b;
    }
    return n;
}

EXPORT void SetInput(unsigned char channel, unsigned char On)
{
    std::lock_guard<std::recursive_mutex> g(lock_);
    if (pMobaLedLib != NULL) pMobaLedLib->Set_Input(channel, On);
}

EXPORT unsigned char GetInput(unsigned char channel)
{
    std::lock_guard<std::recursive_mutex> g(lock_);
    if (pMobaLedLib == NULL) return 0;
    return pMobaLedLib->Get_Input(channel);
}

// Fensterfunktionen: es gibt kein Fenster; der Zustand wird nur gemerkt (die Anzeige macht der Aufrufer)
EXPORT void ShowLEDWindow(unsigned char, unsigned char, unsigned char, unsigned char, int, int, bool) { windowOpen = true; }
EXPORT void CloseLEDWindow() { windowOpen = false; }
EXPORT bool IsLEDWindowVisible() { return windowOpen; }
EXPORT int GetLEDWindowRect(void* rect) { return 0; }   // kein Fenster -> keine Position (int: Aufrufer liest long)
