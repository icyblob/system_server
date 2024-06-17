#pragma once

#include <stdint.h>

extern "C"
{

struct BetInfoOutput
{
    // meta data info
    uint32_t betId;
    uint32_t nOption; // options number
    uint8_t creator[32];
    uint8_t betDesc[32];              // 32 bytes
    uint8_t optionDesc[8 * 32];       // 8x(32)=256bytes
    uint8_t oracleProviderId[8 * 32]; // 256x8=2048bytes
    uint32_t oracleFees[8];           // 4x8 = 32 bytes

    uint8_t openDate[4];  // creation date, start to receive bet
    uint8_t closeDate[4]; // stop receiving bet date
    uint8_t endDate[4];   // result date
    // Amounts and numbers
    uint64_t minBetAmount;
    uint32_t maxBetSlotPerOption;
    uint32_t currentBetState[8]; // how many bet slots have been filled on each option

    // Voting result
    int8_t betResultWonOption[8];
    int8_t betResultOPId[8];
};

struct QuotteryissueBetInput
{
    uint8_t betDesc[32];
    uint8_t optionDesc[32 * 8];
    uint8_t oracleProviderId[32 * 8];
    uint32_t oracleFees[8];
    uint8_t closeDate[4];
    uint8_t endDate[4];
    uint64_t amountPerSlot;
    uint32_t maxBetSlotPerOption;
    uint32_t numberOfOption;
};

// Get a list of current active bet IDs
int quotteryWrapperGetActiveBet(
    const char* nodeIp,
    const int nodePort,
    uint32_t& betCount,
    uint32_t* betIDs);

// Print the information of a bet ID
int quotteryWrapperPrintBetInfo(const char* nodeIp, const int nodePort, int betId);

// Get the bet information
int quotteryWrapperGetBetInfo(
    const char* nodeIp,
    const int nodePort,
    int betId,
    BetInfoOutput& result);

// Join a bet
int quotteryWrapperJoinBet(
    const char* nodeIp,
    int nodePort,
    const char* seed,
    uint32_t betId,
    int numberOfBetSlot,
    uint64_t amountPerSlot,
    uint8_t option,
    uint32_t scheduledTickOffset,
    char* txHash,
    uint32_t& txTick);

// Issue a bet
int quotteryWrapperIssueBet(
    const char* nodeIp,
    int nodePort,
    const char* seed,
    QuotteryissueBetInput betInfo,
    uint32_t scheduledTickOffset,
    char* txHash,
    uint32_t& txTick);
}