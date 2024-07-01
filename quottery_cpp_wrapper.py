import ctypes
from collections import defaultdict
import logging
import time
# Define the C++ Quottery struct wrapper


class QuotteryFeesOutput(ctypes.Structure):
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
    #     // meta data info
    _fields_ = [
        ('betId', ctypes.c_uint32),
        ('nOption', ctypes.c_uint32),  # options number
        ('creator', ctypes.c_uint8 * 32),
        ('betDesc', ctypes.c_uint8 * 32),
        ('optionDesc', ctypes.c_uint8 * 256),  # 8x(32)=256bytes
        ('oracleProviderId', ctypes.c_uint8 * 256),  # 256x8=2048bytes ???
        ('oracleFees', ctypes.c_uint32 * 8),   # 4x8 = 32 bytes

        # Time relate to the bet. The format is [YY, MM, DD, HH, MM, SS]
        ('openDateTime', ctypes.c_uint8 * 6),
        ('closeDateTime', ctypes.c_uint8 * 6),   # stop receiving bet date
        ('endDateTime', ctypes.c_uint8 * 6),       # result date

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
    _fields_ = [
    ('feePerSlotPerDay', ctypes.c_uint64),  # Amount of qus
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

class QuotteryCppWrapper:
    def __init__(self, libs, nodeIP, port, logName=''):

        self.nodeIP = nodeIP
        self.port = port

        log_format = '[%(name)s][%(asctime)s] %(message)s'
        # Configure the logging module to use the custom format
        logging.basicConfig(level=logging.INFO, format=log_format)
        self.logger = logging.getLogger('QTRY_CPP_WRAPPER')
        if logName:
            self.logger = logging.getLogger(logName)

        # Constant parameters
        self.scheduleTickOffset = 5
        self.maxNumberOfOracleProvides = 8

        # Quottery related
        self.quottery_cpp_func = ctypes.CDLL(libs)

        # Key utils functions: PubKey from Indentity
        self.quottery_cpp_func.getPublicKeyFromIdentityWrapper.argtypes = [
            ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint8)]
        self.quottery_cpp_func.getPublicKeyFromIdentityWrapper.restype = ctypes.c_int

        # Key utils functions: Indentity from Pubkey
        self.quottery_cpp_func.getIdentityFromPublicKeyWrapper.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_char_p]
        self.quottery_cpp_func.getIdentityFromPublicKeyWrapper.restype = ctypes.c_int

        # Quottery basic information
        self.quottery_cpp_func.quotteryWrapperGetBasicInfo.argtypes = [
            ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(QtryBasicInfoOutput)]
        self.quottery_cpp_func.quotteryWrapperGetBasicInfo.restype = ctypes.c_int

        # Print the bet infomation
        self.quottery_cpp_func.quotteryWrapperPrintBetInfo.argtypes = [
            ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        self.quottery_cpp_func.quotteryWrapperPrintBetInfo.restype = ctypes.c_int

        # Get a list of active bets ID
        self.quottery_cpp_func.quotteryWrapperGetActiveBet.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32)]
        self.quottery_cpp_func.quotteryWrapperGetActiveBet.restype = ctypes.c_int

        # Get information from a bet ID
        self.quottery_cpp_func.quotteryWrapperGetBetInfo.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(BetInfoOutput)]
        self.quottery_cpp_func.quotteryWrapperGetBetInfo.restype = ctypes.c_int

    def get_qtry_basic_info(self):
        basic_info = {}
        qt_basic_info = QtryBasicInfoOutput()
        sts = self.quottery_cpp_func.quotteryWrapperGetBasicInfo(self.nodeIP.encode(
            'utf-8'), self.port, ctypes.byref(qt_basic_info))

        if sts :
            self.logger.warning('[WARNING] Failed to get qtry basic info')
            return (sts, basic_info)

        # Fill the data in dictionary
        basic_info['fee_per_slot_per_day'] = qt_basic_info.feePerSlotPerDay
        basic_info['game_operator_fee'] = qt_basic_info.gameOperatorFee / 100
        basic_info['share_holder_fee'] = qt_basic_info.shareholderFee / 100
        basic_info['min_bet_slot_amount'] = qt_basic_info.minBetSlotAmount
        basic_info['burn_fee'] = qt_basic_info.burnFee / 100
        basic_info['n_issued_bet'] = qt_basic_info.nIssuedBet
        basic_info['money_flow'] = qt_basic_info.moneyFlow
        basic_info['money_flow_through_issue_bet'] = qt_basic_info.moneyFlowThroughIssueBet
        basic_info['money_flow_through_join_bet'] = qt_basic_info.moneyFlowThroughJoinBet
        basic_info['money_flow_through_finalize_bet'] = qt_basic_info.moneyFlowThroughFinalizeBet
        basic_info['earned_amount_for_share_holder'] = qt_basic_info.earnedAmountForShareHolder
        basic_info['paid_amount_for_share_holder'] = qt_basic_info.paidAmountForShareHolder
        basic_info['earned_amount_for_bet_winner'] = qt_basic_info.earnedAmountForBetWinner
        basic_info['distributed_amount'] = qt_basic_info.distributedAmount
        basic_info['burned_amount'] = qt_basic_info.burnedAmount

        identity_buffer = ctypes.create_string_buffer(60)
        self.quottery_cpp_func.getIdentityFromPublicKeyWrapper(
            qt_basic_info.gameOperator, identity_buffer)
        basic_info['game_operator']= identity_buffer.value.decode('utf-8')

        return sts, basic_info

    def get_bet_info(self, betId):
        bet_info = {}

         # Access the fields of the struct
        qt_output_result = BetInfoOutput()
        sts = self.quottery_cpp_func.quotteryWrapperGetBetInfo(self.nodeIP.encode(
            'utf-8'), self.port, betId, ctypes.byref(qt_output_result))

        if sts:
            self.logger.warning('[WARNING] Failed to get info of active bet ID %d', betId)
            return (sts, bet_info)

        bet_info['bet_id'] = betId
        # Strip the string terminator
        bet_info['bet_desc'] = bytes(
            qt_output_result.betDesc).decode('utf-8').strip('\x00')
        bet_info['no_options'] = qt_output_result.nOption

        identity_buffer = ctypes.create_string_buffer(60)
        self.quottery_cpp_func.getIdentityFromPublicKeyWrapper(
            qt_output_result.creator, identity_buffer)
        bet_info['creator'] = identity_buffer.value.decode('utf-8')

        # Bet fee
        # TODO: Correct the naming in core
        # https://github.com/qubic/core/blob/dkat-quottery-sc/src/contracts/Quottery.h#L524
        bet_info['amount_per_bet_slot'] = qt_output_result.minBetAmount

        # Get the options descriton
        bet_info['option_desc'] = [''.join(chr(
            qt_output_result.optionDesc[i + j]).strip('\x00') for j in range(32)) for i in range(0, 256, 32)]
        bet_info['option_desc'] = [s for s in bet_info['option_desc'] if s]

        bet_info['current_bet_state'] = []
        for i in range(0, bet_info['no_options']):
            bet_info['current_bet_state'].append(qt_output_result.currentBetState[i])

        bet_info['max_slot_per_option'] = qt_output_result.maxBetSlotPerOption

        bet_info['open_date'] = f"{qt_output_result.openDateTime[0]:02}" + '-' + \
            f"{qt_output_result.openDateTime[1]:02}" + \
            '-' + f"{qt_output_result.openDateTime[2]:02}"
        bet_info['open_time'] = f"{qt_output_result.openDateTime[3]:02}" + ':' + \
            f"{qt_output_result.openDateTime[4]:02}" + \
            ':' + f"{qt_output_result.openDateTime[5]:02}"
        
        bet_info['close_date'] = f"{qt_output_result.closeDateTime[0]:02}" + '-' + \
            f"{qt_output_result.closeDateTime[1]:02}" + \
            '-' + f"{qt_output_result.closeDateTime[2]:02}"
        bet_info['close_time'] = f"{qt_output_result.closeDateTime[3]:02}" + ':' + \
            f"{qt_output_result.closeDateTime[4]:02}" + \
            ':' + f"{qt_output_result.closeDateTime[5]:02}"
        
        bet_info['end_date'] = f"{qt_output_result.endDateTime[0]:02}" + '-' + \
            f"{qt_output_result.endDateTime[1]:02}" + \
            '-' + f"{qt_output_result.endDateTime[2]:02}"
        bet_info['end_time'] = f"{qt_output_result.endDateTime[0]:02}" + ':' + \
            f"{qt_output_result.endDateTime[1]:02}" + \
            ':' + f"{qt_output_result.endDateTime[2]:02}"


        # Oracle id and fee. Assume they are follow extract order
        bet_info['oracle_id'] = []
        bet_info['oracle_fee'] = []
        bet_info['oracle_vote'] = []
        for i in range(0, self.maxNumberOfOracleProvides):
            # Pack the oracle ID
            offset = 32 * i
            oracle_id_public_key = ctypes.cast(ctypes.addressof(
                qt_output_result.oracleProviderId) + offset, ctypes.POINTER(ctypes.c_uint8))
            all_zeros = all(value == 0 for value in oracle_id_public_key[:32])
            # Only add if public key is not fully zeros
            if not all_zeros:
                # Append the oracle ID
                identity_buffer = ctypes.create_string_buffer(60)
                self.quottery_cpp_func.getIdentityFromPublicKeyWrapper(
                    oracle_id_public_key, identity_buffer)
                bet_info['oracle_id'].append(identity_buffer.value.decode('utf-8'))

                # Append the oracle ID
                oracle_fee = ctypes.cast(ctypes.addressof(
                    qt_output_result.oracleFees) + i * 4, ctypes.POINTER(ctypes.c_uint32))
                bet_info['oracle_fee'].append(float(oracle_fee[0]) / 100)

                # Init the voting of Oracle as invalid
                bet_info['oracle_vote'].append(-1)
        bet_info['no_ops'] = len(bet_info['oracle_id'])

        # Get the result of the votes
        for i in range(0, self.maxNumberOfOracleProvides):
            op_vote_option = qt_output_result.betResultWonOption[i]
            op_vote_id = qt_output_result.betResultOPId[i]
            if op_vote_option >= 0 and op_vote_id >= 0:
                bet_info['oracle_vote'][op_vote_id] = op_vote_option

        return (0, bet_info)

    def get_active_bets(self):

        # Return bets dictionary
        activeBets ={}

        # Get the active bets id
        arrayPointer = (ctypes.c_uint32 * 1024)()
        numberOfActiveBets = ctypes.c_uint32(0)
        sts = self.quottery_cpp_func.quotteryWrapperGetActiveBet(self.nodeIP.encode(
            'utf-8'), self.port, ctypes.pointer(numberOfActiveBets), arrayPointer)
        if sts:
            self.logger.warning('Get active bets failed!')
            return (sts, activeBets)

        bets_count = numberOfActiveBets.value
        self.logger.info("There are %d bets: %s", bets_count, arrayPointer[0:bets_count])

        # Process each active bet and recording it
        for i in range(0, bets_count):
            bet_id = arrayPointer[i]

            # The bet is inactive. Init it with an empty bet info
            activeBets[bet_id] = {}

            # Print the bet for debugging
            # self.quottery_cpp_func.quotteryWrapperPrintBetInfo(self.nodeIP.encode(
            #     'utf-8'), self.port, bet_id)

            bet_info = {}

            # Access the fields of the struct
            bet_info_sts, bet_info = self.get_bet_info(bet_id)
            # The bet info is failed. Save the last error and process the next one
            if bet_info_sts :
                sts = bet_info_sts
                continue

            # Get the result bet and also set the current date
            number_of_oracle_operators = bet_info['no_ops']
            required_votes = number_of_oracle_operators * 2 /  3
            op_voted_count = 0
            dominated_votes = 0
            vote_count = defaultdict(int)
            op_vote_options = bet_info['oracle_vote']
            for i in range(0, number_of_oracle_operators):
                if op_vote_options[i] > -1:
                    vote_count[op_vote_options[i]] += 1
                    op_voted_count += 1
            # Decide the win option
            ## Find the key with the max value
            if op_voted_count > 0:
                key_with_max_votes = max(vote_count, key=vote_count.get)
                dominated_votes = vote_count[key_with_max_votes]

            ## Check the win condition. This check is replicating the decision in node
            ## If the dominated votes are satisfied the win conditions (>= 2/3 total of OPs)
            if dominated_votes >= required_votes:
                bet_info['result'] = key_with_max_votes
            else:
                # The result is considered invalid
                bet_info['result'] = -1

            # Append the active bets
            activeBets[bet_info['bet_id']] = bet_info

        return (sts, activeBets)


