import unittest
import quottery_rpc_wrapper

qt = quottery_rpc_wrapper.QuotteryRpcWrapper('https://rpc.qubic.org', 'libs/quottery_cpp/lib/libquottery_cpp.so', 'DB_UPDATER')

class TestQtryRpcWrapper(unittest.TestCase):

    def test_get_qtry_basic_info(self):
        sts, qtry_info = qt.get_qtry_basic_info()
        self.assertEqual(sts, 0)
        print(qtry_info)

    def test_get_active_bets(self):
        sts, active_bets = qt.get_active_bets()
        self.assertEqual(sts, 0)
        print(active_bets)

    def test_get_bet_info(self):
        sts, bet_info = qt.get_bet_info(53)
        self.assertEqual(sts, 0)
        print(bet_info)

    def test_get_all_bets(self):
        (sts, activeBets, tick_number) = qt.get_all_bets()
        self.assertEqual(sts, 0)
        print(tick_number)
        print(activeBets)

    def test_get_bet_option_detail(self):
        (sts, bet_option_detail) = qt.get_bet_option_detail(52, 0)
        self.assertEqual(sts, 0)
        print(bet_option_detail)

        (sts, bet_option_detail) = qt.get_bet_option_detail(52, 1)
        self.assertEqual(sts, 0)
        #print(bet_option_detail)

if __name__ == '__main__':
    unittest.main()