import ctypes
from collections import defaultdict
# Define the C++ Quottery struct wrapper


class QuotteryjoinBetInput(ctypes.Structure):
    _fields_ = [
        ("betId", ctypes.c_uint32),
        ("numberOfSlot", ctypes.c_int32),
        ("option", ctypes.c_uint32),
        ("_placeHolder", ctypes.c_uint32)
    ]


class QuotteryissueBetInput(ctypes.Structure):
    _fields_ = [
        ('betDesc', ctypes.c_uint8 * 32),
        ('optionDesc', ctypes.c_uint8 * 256),
        ('oracleProviderId', ctypes.c_uint8 * 256),
        ('oracleFees', ctypes.c_uint32 * 8),
        ('closeDate', ctypes.c_uint8 * 4),
        ('endDate', ctypes.c_uint8 * 4),
        ('amountPerSlot', ctypes.c_uint64),
        ('maxBetSlotPerOption', ctypes.c_uint32),
        ('numberOfOption', ctypes.c_uint32)
    ]


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
        # creation date, start to receive bet
        ('openDate', ctypes.c_uint8 * 4),
        ('closeDate', ctypes.c_uint8 * 4),   # stop receiving bet date
        ('endDate', ctypes.c_uint8 * 4),       # result date
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

# Function to fill the array with the ASCII values of the string characters
def fill_array_from_string(ctypes_array, string, start_index):
    for i, char in enumerate(string):
        ctypes_array[start_index + i] = ord(char)

def pack_date_to_4uint8(s):
    # Extract the day part of the string (first two characters)
    date_str = s.split('-')

    result = (ctypes.c_uint8 * 4)()
    result[0] = int(date_str[0])
    result[1] = int(date_str[1])
    result[2] = int(date_str[2])
    result[3] = 0
    return result


class QuotteryCppWrapper:
    def __init__(self, libs, nodeIP, port):

        self.nodeIP = nodeIP
        self.port = port

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

        # Join a bet
        self.quottery_cpp_func.quotteryWrapperJoinBet.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint32,
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.c_uint8,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_uint32)
        ]
        self.quottery_cpp_func.quotteryWrapperJoinBet.restype = ctypes.c_int

        # Add a bet
        self.quottery_cpp_func.quotteryWrapperIssueBet.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            QuotteryissueBetInput,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_uint32)
        ]
        self.quottery_cpp_func.quotteryWrapperIssueBet.restype = ctypes.c_int

    def get_bet_info(self, betId):
        bet_info = {}

         # Access the fields of the struct
        qt_output_result = BetInfoOutput()
        sts = self.quottery_cpp_func.quotteryWrapperGetBetInfo(self.nodeIP.encode(
            'utf-8'), self.port, betId, ctypes.byref(qt_output_result))

        if sts:
            print('[WARNING] Failed to get info of active bet ID', betId)
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

        bet_info['open_date'] = f"{qt_output_result.openDate[0]:02}" + '-' + \
            f"{qt_output_result.openDate[1]:02}" + \
            '-' + f"{qt_output_result.openDate[2]:02}"
        bet_info['close_date'] = f"{qt_output_result.closeDate[0]:02}" + '-' + \
            f"{qt_output_result.closeDate[1]:02}" + \
            '-' + f"{qt_output_result.closeDate[2]:02}"
        bet_info['end_date'] = f"{qt_output_result.endDate[0]:02}" + '-' + \
            f"{qt_output_result.endDate[1]:02}" + \
            '-' + f"{qt_output_result.endDate[2]:02}"

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
            print('Get active bets failed!')
            return (sts, activeBets)

        bets_count = numberOfActiveBets.value
        print("There are", bets_count, "bets:", arrayPointer[0:bets_count])

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

    def join_bet(self, betInfo):
        # Transaction related
        tx_tick = (ctypes.c_uint32)()
        tx_hash = ctypes.create_string_buffer(60)

        sts = self.quottery_cpp_func.quotteryWrapperJoinBet(
            self.nodeIP.encode('utf-8'),
            self.port,
            betInfo['seed'].encode('utf-8'),
            betInfo['bet_id'],
            betInfo['num_slots'],
            betInfo['amount_per_slot'],
            betInfo['option_id'],
            self.scheduleTickOffset,
            tx_hash,
            ctypes.pointer(tx_tick))
        if  sts!= 0:
            print('Join bet failed!')
            tx_tick = 0
            tx_hash = "0"

        return (tx_hash.value.decode('utf-8'), int(tx_tick.value))

    def add_bet(self, betInfo):
        qt_input_bet = QuotteryissueBetInput()

        # Bet decription
        qt_input_bet.betDesc = (ctypes.c_uint8 * 32)(*
                                                     bytearray(betInfo['bet_desc'].encode('utf-8')))

        # Bet options
        qt_input_bet.numberOfOption = ctypes.c_uint32(betInfo['no_ops'])
        qt_input_bet.optionDesc = (ctypes.c_uint8 * 256)()
        for i in range(betInfo["no_ops"]):
            fill_array_from_string(
                qt_input_bet.optionDesc, betInfo["option_desc"][i], i * 32)

        # Serialize all Oracles ID and convert it to public key.
        num_of_oracles = len(betInfo["oracle_id"])
        if num_of_oracles > 8:
            print("Too much of Oracles. Expect 8 and belows")
        num_of_oracles = min(num_of_oracles, 8)
        qt_input_bet.oracleProviderId = (ctypes.c_uint8 * 256)()
        qt_input_bet.oracleFees = (ctypes.c_uint32 * 8)()

        for i in range(0, num_of_oracles):
            # Pack the oracle ID
            offset = 32 * i
            oracle_id_public_key = ctypes.cast(ctypes.addressof(
                qt_input_bet.oracleProviderId) + offset, ctypes.POINTER(ctypes.c_uint8))
            oracle_id = betInfo["oracle_id"][i]
            self.quottery_cpp_func.getPublicKeyFromIdentityWrapper(
                oracle_id.encode('utf-8'), oracle_id_public_key)
            qt_input_bet.oracleFees[i] = int(betInfo["oracle_fee"][i].replace('.', ''))

        qt_input_bet.closeDate = pack_date_to_4uint8(betInfo['close_date'])
        qt_input_bet.endDate = pack_date_to_4uint8(betInfo['end_date'])

        qt_input_bet.amountPerSlot = ctypes.c_uint64(
            int(betInfo['amount_per_bet_slot']))
        qt_input_bet.maxBetSlotPerOption = ctypes.c_uint32(
            int(betInfo['max_slot_per_option']))

        # Transaction related
        tx_tick = (ctypes.c_uint32)()
        tx_hash = ctypes.create_string_buffer(60)

        # Issue the bet
        sts = self.quottery_cpp_func.quotteryWrapperIssueBet(self.nodeIP.encode(
            'utf-8'), self.port, betInfo['seed'].encode('utf-8'), qt_input_bet, self.scheduleTickOffset, tx_hash, ctypes.pointer(tx_tick))

        if  sts!= 0:
            print('Add bet failed!')
            tx_tick = 0
            tx_hash = "0"

        return (tx_hash.value.decode('utf-8'), int(tx_tick.value))
