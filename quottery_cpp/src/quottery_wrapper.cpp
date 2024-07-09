#include "quottery_wrapper.h"

#include <iostream>
#include <cstring>
#include <map>
#include <chrono>
#include <thread>

#include <keyUtils.h>
#include <quottery.h>
#include <commonFunctions.h>
#include <connection.h>

static const int RESET_CONNECTION_WAIT_IN_SECS = 2;

int quotteryWrapperResetConnection(const char* nodeIp, const int nodePort)
{
    std::cout << "Reseting connection ...\n";
    try
    {
        get_qc(nodeIp, nodePort, true);
        std::this_thread::sleep_for(std::chrono::seconds(RESET_CONNECTION_WAIT_IN_SECS));
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        WrapperStatus::ERROR;
    }

    return WrapperStatus::SUCCESS;
}

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
        quotteryWrapperResetConnection(nodeIp, nodePort);
        std::cerr << e.what() << "\n";
        return WrapperStatus::ERROR;
    }

    // Print for debug
    // quotteryPrintBasicInfo(nodeIp, nodePort);

    // Fill the external struct
    result.feePerSlotPerHour = basicInfo.feePerSlotPerHour;
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

    return WrapperStatus::SUCCESS;
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
        quotteryWrapperResetConnection(nodeIp, nodePort);
        std::cerr << e.what() << '\n';
        return WrapperStatus::ERROR;
    }

    betCount = result.count;
    std::copy(result.betId, result.betId + betCount, betIDs);

    return WrapperStatus::SUCCESS;
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
        quotteryWrapperResetConnection(nodeIp, nodePort);
        return WrapperStatus::ERROR;
    }

    return WrapperStatus::SUCCESS;
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
        quotteryWrapperResetConnection(nodeIp, nodePort);
        return WrapperStatus::ERROR;
    }

    result.betId = betOutput.betId;
    result.nOption = betOutput.nOption;

    std::copy(betOutput.creator, betOutput.creator + 32, result.creator);
    std::copy(betOutput.betDesc, betOutput.betDesc + 32, result.betDesc);
    std::copy(betOutput.optionDesc, betOutput.optionDesc + 8 * 32, result.optionDesc);
    std::copy(
        betOutput.oracleProviderId, betOutput.oracleProviderId + 8 * 32, result.oracleProviderId);
    std::copy(betOutput.oracleFees, betOutput.oracleFees + 8, result.oracleFees);

    // Process the time
    unpackQuotteryDate(result.openDateTime[0],
            result.openDateTime[1],
            result.openDateTime[2],
            result.openDateTime[3],
            result.openDateTime[4],
            result.openDateTime[5],
            betOutput.openDate);

    unpackQuotteryDate(result.closeDateTime[0],
            result.closeDateTime[1],
            result.closeDateTime[2],
            result.closeDateTime[3],
            result.closeDateTime[4],
            result.closeDateTime[5],
            betOutput.closeDate);

    unpackQuotteryDate(result.endDateTime[0],
            result.endDateTime[1],
            result.endDateTime[2],
            result.endDateTime[3],
            result.endDateTime[4],
            result.endDateTime[5],
            betOutput.endDate);

    result.minBetAmount = betOutput.minBetAmount;
    result.maxBetSlotPerOption = betOutput.maxBetSlotPerOption;
    std::copy(betOutput.currentBetState, betOutput.currentBetState + 8, result.currentBetState);

    // Result if there is any
    std::copy(betOutput.betResultOPId, betOutput.betResultOPId + 8, result.betResultOPId);
    std::copy(betOutput.betResultWonOption, betOutput.betResultWonOption + 8, result.betResultWonOption);
    return WrapperStatus::SUCCESS;
}
int quotteryWrapperBetOptionDetail(
    const char* nodeIp,
    const int nodePort,
    uint32_t betId,
    uint32_t betOption,
    uint32_t& numberOfUsers,
    QuotteryBetOptionDetail& result)
{
    numberOfUsers = 0;
    getBetOptionDetail_output betOptionDetail;
    memset(&betOptionDetail, 0, sizeof(getBetOptionDetail_output));

    //quotteryPrintBetOptionDetail(nodeIp, nodePort, betId, betOption);
    try
    {
        quotteryGetBetOptionDetail(nodeIp, nodePort, betId, betOption, betOptionDetail);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        quotteryWrapperResetConnection(nodeIp, nodePort);
        return WrapperStatus::ERROR;
    }

    // The bet does not have any infomation yet
    if (isArrayZero((uint8_t*)&betOptionDetail, sizeof(getBetOptionDetail_output)))
    {
        return WrapperStatus::NO_INFO;
    }

    // Counting the user per options
    std::map<std::string, uint32_t> bettorCount;
    std::map<std::string, uint32_t> bettorIdx;
    char buf[128] = {0};
    for (uint32_t i = 0; i < 1024; i++)
    {
        if (!isZeroPubkey(betOptionDetail.bettor + i * 32))
        {
            memset(buf, 0, 128);
            getIdentityFromPublicKey(betOptionDetail.bettor + i * 32, buf, false);
            std::string id = buf;
            if (bettorCount.count(id) == 0)
            {
                bettorCount[id] = 1;
                bettorIdx[id] = i;
            }
            else
            {
                bettorCount[id]++;
            }
        }
    }

    // Convert data for external use
    numberOfUsers = bettorCount.size();
    uint32_t index = 0;
    for (auto& iter : bettorCount)
    {
        result.bettorAmountOfSlots[index] = iter.second;
        uint32_t user_index = bettorIdx[iter.first];
        std::copy(betOptionDetail.bettor + user_index * 32, betOptionDetail.bettor + user_index * 32 + 32, result.bettor + 32 * index);
        index++;
    }
    return WrapperStatus::SUCCESS;
}

