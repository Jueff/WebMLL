#define CONFIG_ONLY

#include <Arduino.h>
#include "MP3.h"
#include "LEDs_AutoProg.h"

#ifndef MLL_P_MB_PIN1
#define MLL_P_MB_PIN1 255
#endif
#ifndef MLL_P_MB_PIN2
#define MLL_P_MB_PIN2 255
#endif
#ifndef MLL_P_MB_PIN3
#define MLL_P_MB_PIN3 255
#endif
__attribute__((used, section(".mllmb"))) const uint8_t MLL_MB_TAB[12] = {
#if defined(Mainboard_LED1)
  MLL_P_MB_PIN1, 1, (uint8_t)(Mainboard_LED1), (uint8_t)((uint16_t)(Mainboard_LED1) >> 8),
#else
  0, 0, 0, 0,
#endif
#if defined(Mainboard_LED2)
  MLL_P_MB_PIN2, 2, (uint8_t)(Mainboard_LED2), (uint8_t)((uint16_t)(Mainboard_LED2) >> 8),
#else
  0, 0, 0, 0,
#endif
#if defined(Mainboard_LED3)
  MLL_P_MB_PIN3, 3, (uint8_t)(Mainboard_LED3), (uint8_t)((uint16_t)(Mainboard_LED3) >> 8),
#else
  0, 0, 0, 0,
#endif
};

int main()
{
  int r = (int)&Config[0] + (int)&MLL_ConfigRamSize;
  r += (int)&MLL_MB_TAB[0];
#if defined(USE_EXT_ADDR)
  r += (int)&Ext_Addr[0];
#endif
#if defined(USE_LED_TO_VAR)
  r += (int)&LED2Var_Tab[0];
#endif
#if defined(MLL_HAS_STORE_VALUES)
  r += (int)&Store_Values[0];
#endif
#if defined(MLL_HAS_START_VALUES)
  r += (int)&Start_Values_Tab[0];
#endif
  return r;
}
