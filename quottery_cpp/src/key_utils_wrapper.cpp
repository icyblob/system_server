#include "key_utils_wrapper.h"

#include <iostream>

#include <keyUtils.h>

int getPublicKeyFromIdentityWrapper(const char* identity, uint8_t* publicKey)
{
    getPublicKeyFromIdentity(identity, publicKey);
    return 0;
}

int getIdentityFromPublicKeyWrapper(const uint8_t* pubkey, char* identity)
{
    getIdentityFromPublicKey(pubkey, identity, false);
    return 0;
}