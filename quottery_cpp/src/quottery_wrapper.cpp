#include "quottery_wrapper.h"

#include <iostream>

#include <keyUtils.h>
#include <quottery.h>

int quotteryWrapperGetBasicInfo(const char* nodeIp, const int nodePort, QuotteryBasicInfoOutput& result)
{
    // Get the inform with standard api
    qtryBasicInfo_output basicInfo;
    try
    {
        quotteryGetBasicInfo(nodeIp, nodePort, basicInfo);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }

    // Print for debug
    // quotteryPrintBasicInfo(nodeIp, nodePort);

    // Fill the external struct
    result.feePerSlotPerDay = basicInfo.feePerSlotPerDay;
    result.gameOperatorFee = basicInfo.gameOperatorFee;
    result.shareholderFee = basicInfo.shareholderFee;
    result.minBetSlotAmount = basicInfo.minBetSlotAmount;
    result.burnFee = basicInfo.burnFee;
    result.nIssuedBet = basicInfo.nIssuedBet;
    result.moneyFlow = basicInfo.moneyFlow;
    result.moneyFlowThroughIssueBet = basicInfo.moneyFlowThroughIssueBet;
    result.moneyFlowThroughJoinBet = basicInfo.moneyFlowThroughJoinBet;
    result.moneyFlowThroughFinalizeBet = basicInfo.moneyFlowThroughFinalizeBet;
    result.earnedAmountForShareHolder = basicInfo.earnedAmountForShareHolder;
    result.paidAmountForShareHolder = basicInfo.paidAmountForShareHolder;
    result.earnedAmountForBetWinner = basicInfo.earnedAmountForBetWinner;
    result.distributedAmount = basicInfo.distributedAmount;
    result.burnedAmount = basicInfo.burnedAmount;
    std::copy(basicInfo.gameOperator, basicInfo.gameOperator + 32, result.gameOperator);

    return 0;
}

int quotteryWrapperGetActiveBet(
    const char* nodeIp,
    const int nodePort,
    uint32_t& betCount,
    uint32_t* betIDs)
{
    betCount = 0;
    getActiveBet_output result;
    try
    {
        quotteryGetActiveBet(nodeIp, nodePort, result);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }

    betCount = result.count;
    std::copy(result.betId, result.betId + betCount, betIDs);

    return 0;
}

int quotteryWrapperPrintBetInfo(const char* nodeIp, const int nodePort, int betId)
{
    try
    {
        quotteryPrintBetInfo(nodeIp, nodePort, betId);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }

    return 0;
}

// Get the bet information
int quotteryWrapperGetBetInfo(
    const char* nodeIp,
    const int nodePort,
    int betId,
    BetInfoOutput& result)
{
    getBetInfo_output betOutput;
    try
    {
        quotteryGetBetInfo(nodeIp, nodePort, betId, betOutput);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }

    result.betId = betOutput.betId;
    result.nOption = betOutput.nOption;

    std::copy(betOutput.creator, betOutput.creator + 32, result.creator);
    std::copy(betOutput.betDesc, betOutput.betDesc + 32, result.betDesc);
    std::copy(betOutput.optionDesc, betOutput.optionDesc + 8 * 32, result.optionDesc);
    std::copy(
        betOutput.oracleProviderId, betOutput.oracleProviderId + 8 * 32, result.oracleProviderId);
    std::copy(betOutput.oracleFees, betOutput.oracleFees + 8, result.oracleFees);
    std::copy(betOutput.openDate, betOutput.openDate + 4, result.openDate);
    std::copy(betOutput.closeDate, betOutput.closeDate + 4, result.closeDate);
    std::copy(betOutput.endDate, betOutput.endDate + 4, result.endDate);

    result.minBetAmount = betOutput.minBetAmount;
    result.maxBetSlotPerOption = betOutput.maxBetSlotPerOption;
    std::copy(betOutput.currentBetState, betOutput.currentBetState + 8, result.currentBetState);

    // Result if there is any
    std::copy(betOutput.betResultOPId, betOutput.betResultOPId + 8, result.betResultOPId);
    std::copy(betOutput.betResultWonOption, betOutput.betResultWonOption + 8, result.betResultWonOption);
    return 0;
}

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
    uint32_t& txTick)
{
    try
    {
        quotteryJoinBet(
            nodeIp,
            nodePort,
            seed,
            betId,
            numberOfBetSlot,
            amountPerSlot,
            option,
            scheduledTickOffset,
            txHash,
            &txTick);
    }
    catch (const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }

    return 0;
}

// Issue a bet
int quotteryWrapperIssueBet(
    const char* nodeIp,
    int nodePort,
    const char* seed,
    QuotteryissueBetInput betInfo,
    uint32_t scheduledTickOffset,
    char* txHash,
    uint32_t& txTick)
{
    QuotteryissueBet_input betInput;
    std::copy(betInfo.betDesc, betInfo.betDesc + 32, betInput.betDesc);
    std::copy(betInfo.optionDesc, betInfo.optionDesc + 32 * 8, betInput.optionDesc);
    std::copy(
        betInfo.oracleProviderId, betInfo.oracleProviderId + 32 * 8, betInput.oracleProviderId);
    std::copy(betInfo.oracleFees, betInfo.oracleFees + 8, betInput.oracleFees);
    std::copy(betInfo.closeDate, betInfo.closeDate + 4, betInput.closeDate);
    std::copy(betInfo.endDate, betInfo.endDate + 4, betInput.endDate);

    betInput.amountPerSlot = betInfo.amountPerSlot;
    betInput.maxBetSlotPerOption = betInfo.maxBetSlotPerOption;
    betInput.numberOfOption = betInfo.numberOfOption;
    try
    {
        quotteryIssueBet(nodeIp, nodePort, seed, scheduledTickOffset, &betInput, txHash, &txTick);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }

    return 0;
}
