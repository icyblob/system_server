#pragma once

#include <stdint.h>

extern "C"
{
int getPublicKeyFromIdentityWrapper(const char* identity, uint8_t* publicKey);

int getIdentityFromPublicKeyWrapper(const uint8_t* pubkey, char* identity);

}