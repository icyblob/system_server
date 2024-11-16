from collections import defaultdict
import logging
import requests
import time
import ctypes
import base64
import qtry_utils

# Define the rpc Quottery struct wrapper
MESSAGE_HEADERS = {
  'Accept': 'application/json',
  'Content-Type': 'application/json',
}

API_PATH = '/v1/querySmartContract'
TICK_INFO_PATH = '/v1/tick-info'

QTRY_CONTRACT_INDEX = 2
QTRY_GET_BASIC_INFO = 1
QTRY_GET_BET_INFO = 2
QTRY_GET_BET_OPTION_DETAIL = 3
QTRY_GET_ACTIVE_BET = 4
QTRY_GET_BET_BY_CREATOR = 5

QTRY_GET_STRING = {
    QTRY_GET_BASIC_INFO : "GetBasicInfo",
    QTRY_GET_BET_INFO : "GetBetInfo",
    QTRY_GET_BET_OPTION_DETAIL : "GetBetOptionDetail",
    QTRY_GET_ACTIVE_BET : "GetActiveBet",
    QTRY_GET_BET_BY_CREATOR : "GetBetByCreator"
}

def makeJsonData(contractIndex, inputType, inputSize, requestData):
    return {
        'contractIndex': contractIndex,
        'inputType': inputType,
        'inputSize': inputSize,
        'requestData': requestData
    }

class QuotteryRpcWrapper:
    """Class allow requesting data from http endpoint"""
    def __init__(self, address, libFile, logName=''):
        """
        Args:
            apiUri (str): The full path to quottery http endpoint
            logName (str, optional): The name of the logging, default is empty
        """

        log_format = '[%(name)s][%(asctime)s] %(message)s'
        # Configure the logging module to use the custom format
        logging.basicConfig(level=logging.INFO, format=log_format)
        self.logger = logging.getLogger('QTRY_HTTP_WRAPPER')
        if logName:
            self.logger = logging.getLogger(logName)

        # Quottery lib related function. Need to call K12 function
        self.quottery_cpp_func = ctypes.CDLL(libFile)

        # Key utils functions: PubKey from Indentity
        self.quottery_cpp_func.getPublicKeyFromIdentityWrapper.argtypes = [
            ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint8)]
        self.quottery_cpp_func.getPublicKeyFromIdentityWrapper.restype = ctypes.c_int

        # Key utils functions: Indentity from Pubkey
        self.quottery_cpp_func.getIdentityFromPublicKeyWrapper.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_char_p]
        self.quottery_cpp_func.getIdentityFromPublicKeyWrapper.restype = ctypes.c_int

        # Constant parameters
        self.httpEndPoint = address
        self.apiUri = self.httpEndPoint + API_PATH
        self.tickInfoUri = self.httpEndPoint + TICK_INFO_PATH
        self.scheduleTickOffset = 5
        self.maxNumberOfOracleProvides = 8
        self.maxIdsPerOption = 1024

    def get_qtry_response(self, json_data):
        try:
            response = requests.post(
                self.apiUri, headers = MESSAGE_HEADERS, json = json_data)
            response.raise_for_status()  # Raise an error for bad status codes
            result = response.json()  # Parse the JSON response
            return result
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)
            debug_request = 'Unknown'
            if json_data['inputType'] in QTRY_GET_STRING:
                debug_request =  QTRY_GET_STRING[json_data['inputType']]
            self.logger.warning('[WARNING] Failed to get qtry respond for %s. Retry later.', debug_request)
            return None

    def get_qtry_basic_info(self):
        """Gets the quottery basic information

        Returns:
            sts (int): status of request. 0 is success, otherwise is failure
            dict: a dictionary that contain information about quottery basic information. If failure, it is empty
        """
        json_data = makeJsonData(QTRY_CONTRACT_INDEX, QTRY_GET_BASIC_INFO, 0, "")
        response_data = self.get_qtry_response(json_data)

        basic_info = {}
        sts = 0
        if response_data == None :
            sts = 1
            self.logger.warning('[WARNING] Failed to get qtry basic info')
            return (sts, basic_info)

        data =  base64.b64decode(response_data['responseData'])
        qt_basic_info = qtry_utils.QtryBasicInfoOutput.from_buffer_copy(data)

        # Fill the data in dictionary
        basic_info['fee_per_slot_per_hour'] = qt_basic_info.feePerSlotPerHour
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
        basic_info['game_operator'] = identity_buffer.value.decode('utf-8')

        return sts, basic_info

    def get_active_bets(self):
        """Gets the number of active bet

        Args:
            None

        Returns:
            sts (int): status of request. 0 is success, otherwise is failure
            number (int): number of active bet
        """
        active_bets = []
        number_of_active_bets = 0
        json_data = makeJsonData(QTRY_CONTRACT_INDEX, QTRY_GET_ACTIVE_BET, 0, "")
        response_data = self.get_qtry_response(json_data)
        sts = 0
        if response_data == None :
            sts = 1
            self.logger.warning('[WARNING] Failed to get active bet')
            return (sts, active_bets)

        data =  base64.b64decode(response_data['responseData'])
        # Extract the first 4 bytes as number of active bets
        number_of_active_bets = int.from_bytes(data[:4], byteorder='little')

        # Extract active bets
        for i in range(1, number_of_active_bets + 1):
            next_4_bytes = data[4 * i : 4 * i + 4]
            next_integer = int.from_bytes(next_4_bytes, byteorder='little')
            active_bets.append(next_integer)

        return sts, active_bets

    def get_bet_info(self, betId):
        """Gets the information of a specific bet

        Args:
            betId (int): The ID of the bet

        Returns:
            sts (int): status of request. 0 is success, otherwise is failure
            dict: a dictionary that contain information about bet information. If failure, it is empty
        """
        bet_info = {}

        input_base64 = base64.b64encode(betId.to_bytes(4, byteorder='little', signed=False)).decode('ascii')
        json_data = makeJsonData(QTRY_CONTRACT_INDEX, QTRY_GET_BET_INFO, 4, input_base64)
        response_data = self.get_qtry_response(json_data)
        sts = 0
        if response_data == None :
            sts = 1
            self.logger.warning('WARNING] Failed to get info of bet ID %d', betId)
            return (sts, bet_info)

        data =  base64.b64decode(response_data['responseData'])
        qt_output_result = qtry_utils.BetInfoOutput.from_buffer_copy(data)

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

        openDateTime = qtry_utils.unpack_date(qt_output_result.openDateTime)
        bet_info['open_date'] = f"{openDateTime[0]:02}" + '-' + \
            f"{openDateTime[1]:02}" + \
            '-' + f"{openDateTime[2]:02}"
        bet_info['open_time'] = f"{openDateTime[3]:02}" + ':' + \
            f"{openDateTime[4]:02}" + \
            ':' + f"{openDateTime[5]:02}"

        closeDateTime = qtry_utils.unpack_date(qt_output_result.closeDateTime)
        bet_info['close_date'] = f"{closeDateTime[0]:02}" + '-' + \
            f"{closeDateTime[1]:02}" + \
            '-' + f"{closeDateTime[2]:02}"
        bet_info['close_time'] = f"{closeDateTime[3]:02}" + ':' + \
            f"{closeDateTime[4]:02}" + \
            ':' + f"{closeDateTime[5]:02}"

        endDateTime = qtry_utils.unpack_date(qt_output_result.endDateTime)
        bet_info['end_date'] = f"{endDateTime[0]:02}" + '-' + \
            f"{endDateTime[1]:02}" + \
            '-' + f"{endDateTime[2]:02}"
        bet_info['end_time'] = f"{endDateTime[3]:02}" + ':' + \
            f"{endDateTime[4]:02}" + \
            ':' + f"{endDateTime[5]:02}"


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

    def get_all_bets(self):
        """Gets the information of all bet that respond from node

        Returns:
            sts (int): status of request. 0 is success, otherwise is failure
            list: list of dictionary that contain information about all bet information. If failure, it is empty
        """

        # Return bets dictionary
        activeBets ={}

        # Get the active bets id
        sts, active_bets_list = self.get_active_bets()
        if sts:
            self.logger.warning('Get bets from node failed!')
            return (sts, activeBets, 0)

        bets_count = len(active_bets_list)
        self.logger.info("Server responds %d bets", bets_count)

        # The number of bet that can get information from node
        bet_info_count = 0
        # Process each active bet and recording it
        for i in range(0, bets_count):
            bet_id = active_bets_list[i]

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

            bet_info_count = bet_info_count + 1

        # Only report the tick number if all bets has been respond from node
        tick_number = 0
        if bet_info_count == bets_count:
            # Get current tick number
            try:
                response = requests.get(self.tickInfoUri)
                response.raise_for_status()  # Raise an error for bad status codes
                result = response.json()  # Parse the JSON response
                tick_number = result['tickInfo']['tick']
            except requests.exceptions.RequestException as e:
                self.logger.warning('Get current tick number failed!')

        return (sts, activeBets, tick_number)

    def get_bet_option_detail(self, betID, betOption):
        """Gets the detail of a specific bet and bet option

        Args:
            betID (int): The ID of the bet
            betOption (int): The option ID of this bet

        Returns:
            sts (int): status of request. 0 is success, otherwise is failure
            dict: a dictionary that contain user id and the number of slots of this bet option. If failure, it is empty
        """

        # Return users detail dictionary
        bet_option_detail = {}

        request_data = [betID, betOption]
        bytes_data = b''.join(value.to_bytes(4, byteorder='little', signed=False) for value in request_data)
        input_base64 = base64.b64encode(bytes_data).decode('ascii')
        json_data = makeJsonData(QTRY_CONTRACT_INDEX, QTRY_GET_BET_OPTION_DETAIL, 8, input_base64)
        response_data = self.get_qtry_response(json_data)
        sts = 0
        if response_data == None :
            sts = 1
            return (sts, bet_option_detail)

        data =  base64.b64decode(response_data['responseData'])
        all_zeros = all(value == 0 for value in data)
        # The bet does not have any infomation yet
        if all_zeros:
            sts = 1
            return (sts, bet_option_detail)

        for i in range(0, len(data), 32):
            pubkey = data[i:i + 32]
            all_zeros = all(value == 0 for value in pubkey)
            # Only compute id if public key is not fully zeros
            if all_zeros:
                continue

            # Append the oracle ID
            oracle_id_public_key = ctypes.cast(pubkey, ctypes.POINTER(ctypes.c_uint8))
            identity_buffer = ctypes.create_string_buffer(60)
            self.quottery_cpp_func.getIdentityFromPublicKeyWrapper(
                oracle_id_public_key, identity_buffer)
            user_id = identity_buffer.value.decode('utf-8')
            if user_id in bet_option_detail:
                bet_option_detail[user_id] += 1
            else:
                bet_option_detail[user_id] = 1

        return (sts, bet_option_detail)
