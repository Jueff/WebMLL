#ifndef __ARDUINO_H__
#define __ARDUINO_H__

#include <iostream>

#include <cstdint>
#include <chrono>
#include <time.h>
#include <math.h>
#include <ctime>

#ifdef _WIN32
#define uint8_t unsigned char
#define uint16_t unsigned short
#define uint32_t unsigned long
#else
#include <stdint.h>
#endif

#define OUTPUT 1

using namespace std;

#include <stdio.h>
#include <stdarg.h>

long millis();

uint8_t digitalRead(uint8_t pin);
void digitalWrite(uint8_t pin, uint8_t value);
void pinMode(uint8_t pin, uint8_t mode);

#define PROGMEM
//uint8_t inline pgm_read_byte_near(const void* add) { return *(uint8_t*)add; }
//uint8_t inline pgm_read_word_near(const void* add) { return *(uint16_t*)add; }
//uint8_t inline pgm_read_dword_near(const void* add) { return *(uint32_t*)add; }

#define pgm_read_byte_near *(uint8_t*)
#define pgm_read_word_near *(uint16_t*)
#define pgm_read_dword_near *(uint32_t*)

#endif