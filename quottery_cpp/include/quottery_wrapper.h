#pragma once

#include <stdint.h>

extern "C"
{

enum WrapperStatus
{
    SUCCESS = 0,
    ERROR = 1,
    NO_INFO = 2
};

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

    // Below time will folow [YY, MM, DD, HH, MM, SS]
    uint8_t openDateTime[6];  // creation date, start to receive bet
    uint8_t closeDateTime[6]; // stop receiving bet date
    uint8_t endDateTime[6];   // result date

    // Amounts and numbers
    uint64_t minBetAmount;
    uint32_t maxBetSlotPerOption;
    uint32_t currentBetState[8]; // how many bet slots have been filled on each option

    // Voting result
    int8_t betResultWonOption[8];
    int8_t betResultOPId[8];
};

struct QuotteryBasicInfoOutput
{
    uint64_t feePerSlotPerHour; // Amount of qus
    uint64_t gameOperatorFee; // 4 digit number ABCD means AB.CD% | 1234 is 12.34%
    uint64_t shareholderFee; // 4 digit number ABCD means AB.CD% | 1234 is 12.34%
    uint64_t minBetSlotAmount; // amount of qus
    uint64_t burnFee; // percentage
    uint64_t nIssuedBet; // number of issued bet
    uint64_t moneyFlow;
    uint64_t moneyFlowThroughIssueBet;
    uint64_t moneyFlowThroughJoinBet;
    uint64_t moneyFlowThroughFinalizeBet;
    uint64_t earnedAmountForShareHolder;
    uint64_t paidAmountForShareHolder;
    uint64_t earnedAmountForBetWinner;
    uint64_t distributedAmount;
    uint64_t burnedAmount;
    uint8_t gameOperator[32];
};

struct QuotteryBetOptionDetail
{
    uint8_t bettor[32 * 1024];
    uint32_t bettorAmountOfSlots[1024];
};

// Get quottery basic information
int quotteryWrapperGetBasicInfo(const char* nodeIp, const int nodePort, QuotteryBasicInfoOutput& result);

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

// Get the options detail of a bet
int quotteryWrapperBetOptionDetail(
    const char* nodeIp,
    const int nodePort,
    uint32_t betId,
    uint32_t betOption,
    uint32_t& numberOfUsers,
    QuotteryBetOptionDetail& result);
}

