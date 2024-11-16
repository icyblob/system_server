import ctypes

class QtryBasicInfoOutput(ctypes.Structure):
    """Wrapper struct for accessing QtryBasicInfoOutput in quottery_cpp library"""
    _fields_ = [
    ('feePerSlotPerHour', ctypes.c_uint64),  # Amount of qus
    ('gameOperatorFee', ctypes.c_uint64),  # 4 digit number ABCD means AB.CD% | 1234 is 12.34%
    ('shareholderFee', ctypes.c_uint64),   # 4 digit number ABCD means AB.CD% | 1234 is 12.34%
    ('minBetSlotAmount', ctypes.c_uint64), # amount of qus
    ('burnFee', ctypes.c_uint64),          # percentage
    ('nIssuedBet', ctypes.c_uint64),       # number of issued bet
    ('moneyFlow', ctypes.c_uint64),
    ('moneyFlowThroughIssueBet', ctypes.c_uint64),
    ('moneyFlowThroughJoinBet', ctypes.c_uint64),
    ('moneyFlowThroughFinalizeBet', ctypes.c_uint64),
    ('earnedAmountForShareHolder', ctypes.c_uint64),
    ('paidAmountForShareHolder', ctypes.c_uint64),
    ('earnedAmountForBetWinner', ctypes.c_uint64),
    ('distributedAmount', ctypes.c_uint64),
    ('burnedAmount', ctypes.c_uint64),
    ('gameOperator', ctypes.c_uint8 * 32)
    ]


class QuotteryFeesOutput(ctypes.Structure):
    """Wrapper struct for accessing QuotteryFeesOutput in quottery_cpp library"""
    _fields_ = [
        ('feePerSlotPerDay', ctypes.c_uint64),  # Amount of qus
        ('gameOperatorFee', ctypes.c_uint64),  # Amount of qus
        # 4 digit number ABCD means AB.CD% | 1234 is 12.34%
        ('shareholderFee', ctypes.c_uint64),
        # 4 digit number ABCD means AB.CD% | 1234 is 12.34%
        ('minBetSlotAmount', ctypes.c_uint64),
        ('gameOperatorPubkey', ctypes.c_uint8 * 32)
    ]

class BetInfoOutput(ctypes.Structure):
    """Wrapper struct for accessing BetInfoOutput in quottery_cpp library"""
    _fields_ = [
        ('betId', ctypes.c_uint32),
        ('nOption', ctypes.c_uint32),  # options number
        ('creator', ctypes.c_uint8 * 32),
        ('betDesc', ctypes.c_uint8 * 32),
        ('optionDesc', ctypes.c_uint8 * 256),  # 8x(32)=256bytes
        ('oracleProviderId', ctypes.c_uint8 * 256),  # 256x8=2048bytes ???
        ('oracleFees', ctypes.c_uint32 * 8),   # 4x8 = 32 bytes

        # Packed time relate to the bet. The format is [YY, MM, DD, HH, MM, SS]
        ('openDateTime', ctypes.c_uint32),
        ('closeDateTime', ctypes.c_uint32),   # stop receiving bet date
        ('endDateTime', ctypes.c_uint32),       # result date

        #     // Amounts and numbers
        ('minBetAmount', ctypes.c_uint64),
        ('maxBetSlotPerOption', ctypes.c_uint32),
        # how many bet slots have been filled on each option
        ('currentBetState', ctypes.c_uint32 * 8),

        # Voting result
        ## Vote of each oracle provider chose
        ## -1 mean invalid
        ('betResultWonOption', ctypes.c_int8 * 8),
        ## List of oracle providers that attend to the voting
        ## -1 mean in valid
        ('betResultOPId', ctypes.c_int8 * 8)
    ]

class QtryBasicInfoOutput(ctypes.Structure):
    """Wrapper struct for accessing QtryBasicInfoOutput in quottery_cpp library"""
    _fields_ = [
    ('feePerSlotPerHour', ctypes.c_uint64),  # Amount of qus
    ('gameOperatorFee', ctypes.c_uint64),  # 4 digit number ABCD means AB.CD% | 1234 is 12.34%
    ('shareholderFee', ctypes.c_uint64),   # 4 digit number ABCD means AB.CD% | 1234 is 12.34%
    ('minBetSlotAmount', ctypes.c_uint64), # amount of qus
    ('burnFee', ctypes.c_uint64),          # percentage
    ('nIssuedBet', ctypes.c_uint64),       # number of issued bet
    ('moneyFlow', ctypes.c_uint64),
    ('moneyFlowThroughIssueBet', ctypes.c_uint64),
    ('moneyFlowThroughJoinBet', ctypes.c_uint64),
    ('moneyFlowThroughFinalizeBet', ctypes.c_uint64),
    ('earnedAmountForShareHolder', ctypes.c_uint64),
    ('paidAmountForShareHolder', ctypes.c_uint64),
    ('earnedAmountForBetWinner', ctypes.c_uint64),
    ('distributedAmount', ctypes.c_uint64),
    ('burnedAmount', ctypes.c_uint64),
    ('gameOperator', ctypes.c_uint8 * 32)
    ]

class QtryBetOptionDetail(ctypes.Structure):
    """Wrapper struct for accessing QtryBetOptionDetail in quottery_cpp library"""
    _fields_ = [
        ('bettor', ctypes.c_uint8 * 32 * 1024)
    ]

def QTRY_GET_YEAR(data):
    return (data >> 26) + 24

def QTRY_GET_MONTH(data):
    return (data >> 22) & 0b1111

def QTRY_GET_DAY(data):
    return (data >> 17) & 0b11111

def QTRY_GET_HOUR(data):
    return (data >> 12) & 0b11111

def QTRY_GET_MINUTE(data):
    return (data >> 6) & 0b111111

def QTRY_GET_SECOND(data):
    return data & 0b111111

# Unpack date to [YY, MM, DD, HH, MM, SS] from a uin32_t
def unpack_date(data):
    YY_MM_DD_HH_MM_SS = [0] * 6
    YY_MM_DD_HH_MM_SS[0] = QTRY_GET_YEAR(data)
    YY_MM_DD_HH_MM_SS[1] = QTRY_GET_MONTH(data)
    YY_MM_DD_HH_MM_SS[2] = QTRY_GET_DAY(data)
    YY_MM_DD_HH_MM_SS[3] = QTRY_GET_HOUR(data)
    YY_MM_DD_HH_MM_SS[4] = QTRY_GET_MINUTE(data)
    YY_MM_DD_HH_MM_SS[5] = QTRY_GET_SECOND(data)

    return YY_MM_DD_HH_MM_SS