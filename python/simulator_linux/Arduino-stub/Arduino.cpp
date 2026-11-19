#include "Arduino.h"

#include <stdio.h>
#include <stdarg.h>
#include <ctype.h>
#ifdef _WIN32
#include <Windows.h>
#endif
#include <ostream>
#include <sstream>
#include <string>

using std::chrono::system_clock;

using namespace std;


long millis() 
{
#ifdef _WIN32
    auto ret = GetTickCount();
#else
    auto ret = (long)std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
#endif

    /*TCHAR s[256];
    swprintf(s, 256, L"millis = %d\n", ret);
    OutputDebugString((LPCWSTR)s);
    */
    return ret;
}

uint8_t digitalRead(uint8_t pin) { return 0; }
void digitalWrite(uint8_t pin, uint8_t value) {}
void pinMode(uint8_t pin, uint8_t mode) {}
