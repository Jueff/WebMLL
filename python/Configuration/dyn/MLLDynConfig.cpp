#define CONFIG_ONLY

#include <Arduino.h>
#include "MP3.h"
#include "LEDs_AutoProg.h"

int main()
{
  int r = (int)&Config[0] + (int)&MLL_ConfigRamSize;
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
