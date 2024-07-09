#pragma once

#include <stdint.h>

extern "C"
{

int getTickNumberFromNode(const char* nodeIp, const int nodePort, uint32_t& currentTickNumber);

}