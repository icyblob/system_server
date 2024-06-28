import os
import sys
import sqlite3
import json
import quottery_cpp_wrapper
from threading import Thread
import time
from datetime import datetime, timezone
import argparse
import logging

log_format = '[%(name)s][%(asctime)s] %(message)s'
# Configure the logging module to use the custom format
logging.basicConfig(level=logging.INFO, format=log_format)

# Example usage of the logger
logger = logging.getLogger('DB_UPDATER')

# Init default parameters
NODE_IP = None
NODE_PORT = None
DATABASE_PATH = "."

QUOTTERY_LIBS = 'libs/quottery_cpp/lib/libquottery_cpp.so'
qt = None

DATABASE_FILE = 'database.db'
UPDATE_INTERVAL = 3  # seconds


def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quottery_info (
            bet_id INTEGER PRIMARY KEY,
            no_options INTEGER NOT NULL,
            creator TEXT NOT NULL,
            bet_desc TEXT NOT NULL,
            option_desc TEXT NOT NULL,
            current_bet_state TEXT,
            max_slot_per_option INTEGER NOT NULL,
            amount_per_bet_slot REAL NOT NULL,
            open_date TEXT,
            close_date TEXT,
            end_date TEXT,
            open_time TEXT,
            close_time TEXT,
            end_time TEXT,
            result INTEGER,
            no_ops INTEGER,
            oracle_id TEXT,
            oracle_fee REAL,
            oracle_vote TEXT,
            status INTEGER,
            current_num_selection TEXT,
            current_total_qus TEXT,
            betting_odds TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_bet_info (
            user_bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bet_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            option_id INTEGER NOT NULL,
            num_slots INTEGER NOT NULL,
            amount_per_slot REAL NOT NULL,
            FOREIGN KEY (bet_id) REFERENCES quottery_info(bet_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_basic_info (
            ip TEXT,
            port INTEGER,
            fee_per_slot_per_day INTEGER,
            min_amount_per_slot INTEGER,
            game_operator_fee REAL,
            shareholders_fee REAL,
            burn_fee REAL,
            num_issued_bet INTEGER,
            moneyflow INTEGER,
            moneyflow_through_issuebet INTEGER,
            moneyflow_through_joinbet INTEGER,
            moneyflow_through_finalize INTEGER,
            shareholders_earned_amount INTEGER,
            shareholders_paid_amount INTEGER,
            winners_earned_amount INTEGER,
            distributed_amount INTEGER,
            burned_amount INTEGER,
            game_operator_id TEXT,
            PRIMARY KEY (ip, port)
        )
    ''')
    conn.commit()
    conn.close()

def get_qtry_basic_info_from_node():
    # Connect to the node and get current basic info of qtry
    try:
        sts, qtry_basic_info = qt.get_qtry_basic_info()
        return (sts, qtry_basic_info)
    except Exception as e:
        logger.warning(f"Error get active basic info of qtry from node: {e}")
        return 1, {}

def fetch_active_bets_from_node():
    # Connect to the node and get current active bets
    try:
        sts, active_bets = qt.get_active_bets()
        return (sts, active_bets)
    except Exception as e:
        logger.warning(f"Error fetching active bets from node: {e}")
        return (1, {})

def get_bet_info_from_node(betId):
    try:
        sts, betInfo = qt.get_bet_info(betId)
        return (sts, betInfo)
    except Exception as e:
        logger.warning(f"Error fetching active bets from node: {e}")
        return 1, {}

def check_primary_key_exists(cursor, table_name, primary_key_column, primary_key_value):
    """
    Check if a primary key exists in the table.

    :param cursor: SQLite cursor object.
    :param table_name: Name of the table.
    :param primary_key_column: Name of the primary key column.
    :param primary_key_value: Value of the primary key to check.
    :return: True if the primary key exists, False otherwise.
    """
    query = f"SELECT 1 FROM {table_name} WHERE {primary_key_column} = ?"
    cursor.execute(query, (primary_key_value,))
    return cursor.fetchone() is not None


def update_current_total_qus(conn, bet_id):
    cursor = conn.cursor()

    # Fetch current_bet_state and amount_per_bet_slot
    cursor.execute('''
        SELECT current_bet_state, amount_per_bet_slot
        FROM quottery_info
        WHERE bet_id = ?
    ''', (bet_id,))
    row = cursor.fetchone()

    if row:
        current_bet_state = json.loads(row[0])
        amount_per_bet_slot = row[1]
        total_selections = sum(current_bet_state)
        current_total_qus = total_selections * amount_per_bet_slot

        # Update current_total_qus in the database
        cursor.execute('''
            UPDATE quottery_info
            SET current_total_qus = ?
            WHERE bet_id = ?
        ''', (current_total_qus, bet_id))

    conn.commit()


def update_betting_odds(conn, bet_id):
    # Retrieve current_bet_state for the given bet_id
    cur = conn.cursor()
    cur.execute("SELECT current_bet_state FROM quottery_info WHERE bet_id = ?", (bet_id,))
    row = cur.fetchone()

    if row:
        # TODO: verify this
        current_bet_state = json.loads(row[0])
        total_selections = sum(current_bet_state)

        # Calculate betting odds
        if total_selections == 0:
            betting_odds = [1] * len(current_bet_state)
        else:
            betting_odds = [total_selections / selection if selection > 0 else total_selections for selection in
                            current_bet_state]

        betting_odds = [f'"{e}"' for e in betting_odds]
        betting_odds_str = "[" + ','.join(betting_odds) + "]"

        # Update the betting_odds in the database
        cur.execute("UPDATE quottery_info SET betting_odds = ? WHERE bet_id = ?", (betting_odds_str, bet_id))


def update_database_with_active_bets():
    while True:
        try:
            sts, active_bets = fetch_active_bets_from_node()

            # Verify the active_bets
            if not active_bets:
                logger.warning('[WARNING] Active bets from node is empty! Display the local database')

            sts, qt_basic_info = get_qtry_basic_info_from_node()
            if not qt_basic_info:
                logger.warning('[WARNING] Basic info from node is empty!')
            else:
                # Connect to the database
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute(f'''
                    INSERT OR REPLACE INTO node_basic_info (
                        ip,
                        port,
                        fee_per_slot_per_day,
                        min_amount_per_slot,
                        game_operator_fee,
                        shareholders_fee,
                        burn_fee,
                        num_issued_bet,
                        moneyflow,
                        moneyflow_through_issuebet,
                        moneyflow_through_joinbet,
                        moneyflow_through_finalize,
                        shareholders_earned_amount,
                        shareholders_paid_amount,
                        winners_earned_amount,
                        distributed_amount,
                        burned_amount,
                        game_operator_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                    NODE_IP,
                    NODE_PORT,
                    qt_basic_info['fee_per_slot_per_day'],
                    qt_basic_info['min_bet_slot_amount'],
                    qt_basic_info['game_operator_fee'],
                    qt_basic_info['share_holder_fee'],
                    qt_basic_info['burn_fee'],
                    qt_basic_info['n_issued_bet'],
                    qt_basic_info['money_flow'],
                    qt_basic_info['money_flow_through_issue_bet'],
                    qt_basic_info['money_flow_through_join_bet'],
                    qt_basic_info['money_flow_through_finalize_bet'],
                    qt_basic_info['earned_amount_for_share_holder'],
                    qt_basic_info['paid_amount_for_share_holder'],
                    qt_basic_info['earned_amount_for_bet_winner'],
                    qt_basic_info['distributed_amount'],
                    qt_basic_info['burned_amount'],
                    qt_basic_info['game_operator']
                ))

                conn.commit()
                conn.close()

            # Get the bet ids from db
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute(f"SELECT bet_id FROM quottery_info")
            db_bet_ids = cursor.fetchall()
            db_bet_ids = [row[0] for row in db_bet_ids]
            conn.close()

            # Update the database
            # TODO: Verify the existed one ? Or just update the newest one that is verified from node
            active_bet_ids = []
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            for key, active_bet in active_bets.items():
                active_bet_ids.append(key)
                # Update the database if the bet info is valid
                if active_bet:
                    # Check the bet from node is inactive
                    ## Result checking
                    bet_status = 1
                    if active_bet['result'] >= 0:
                        bet_status = 0
                    else: ## Datetime checking
                        ### Convert the string to a datetime object
                        date_end = datetime.strptime(active_bet['end_date'], '%y-%m-%d').replace(tzinfo=timezone.utc)
                        current_utc_date = datetime.now(timezone.utc)
                        if current_utc_date > date_end:
                            bet_status = 0
                    cursor.execute('''
                        INSERT OR REPLACE INTO quottery_info (
                                    bet_id,
                                    no_options,
                                    creator,
                                    bet_desc,
                                    option_desc,
                                    current_bet_state,
                                    max_slot_per_option,
                                    amount_per_bet_slot,
                                    open_date,
                                    close_date,
                                    end_date,
                                    open_time,
                                    close_time,
                                    end_time,
                                    result,
                                    no_ops,
                                    oracle_id,
                                    oracle_fee,
                                    oracle_vote,
                                    status,
                                    current_num_selection,
                                    current_total_qus,
                                    betting_odds)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                        active_bet['bet_id'],
                        active_bet['no_options'],
                        active_bet['creator'],
                        active_bet['bet_desc'],
                        json.dumps(active_bet['option_desc']),  # This should be a separate table
                        json.dumps(active_bet['current_bet_state']),
                        active_bet['max_slot_per_option'],
                        active_bet['amount_per_bet_slot'],
                        active_bet['open_date'],
                        active_bet['close_date'],
                        active_bet['end_date'],
                        active_bet['open_time'],
                        active_bet['close_time'],
                        active_bet['end_time'],
                        active_bet['result'],
                        active_bet['no_ops'],
                        json.dumps(active_bet['oracle_id']),  # This should be a separate table
                        json.dumps(active_bet['oracle_fee']),  # This should be a separate table
                        json.dumps(active_bet['oracle_vote']),  # This should be a separate table
                        bet_status,
                        json.dumps(active_bet['current_bet_state']),
                        '0',
                        json.dumps(['1'] * active_bet['no_options']),
                    ))
                    update_betting_odds(conn, key)
                    update_current_total_qus(conn, key)


            inactive_bet_ids = set(db_bet_ids) - set(active_bet_ids)
            # Mark the old bet status as 0
            update_statement = 'UPDATE quottery_info SET status = 0 WHERE bet_id IN ({});'.format(
                ','.join('?' for _ in inactive_bet_ids))
            cursor.execute(update_statement, list(inactive_bet_ids))

            conn.commit()
            conn.close()
        except Exception as e:
           logger.warning(f"Error updating database: {e}")
        finally:
            time.sleep(UPDATE_INTERVAL)  # Wait for 3 seconds before the next update

if __name__ == '__main__':
    # Init parameters with environment variables
    if os.getenv('DEBUG_MODE'):
        DEBUG_MODE = os.getenv('DEBUG_MODE')

    if os.getenv('NODE_IP'):
        NODE_IP = os.getenv('NODE_IP')

    if os.getenv('NODE_PORT'):
        NODE_PORT = int(os.getenv('NODE_PORT'))

    if os.getenv('DATABASE_PATH'):
        DATABASE_PATH = os.getenv('DATABASE_PATH')


    # Create the parser
    parser = argparse.ArgumentParser(description='Database update for qtry.')

    # Arguments
    parser.add_argument('-nodeip', type=str, help='Node IP address')
    parser.add_argument('-nodeport', type=int, help='Node port number')
    parser.add_argument('-dbpath', type=str, help='Directory contain the database file')

    # Execute the parse_args() method
    args = parser.parse_args()

    # Access the arguments and overwrite them
    if args.nodeip:
        NODE_IP = args.nodeip
    if args.nodeport:
        NODE_PORT = args.nodeport
    if args.dbpath:
        DATABASE_PATH = args.dbpath
    DATABASE_FILE = os.path.join(DATABASE_PATH, DATABASE_FILE)

    # Print the configuration to verify
    logger.info("Launch the database update with configurations")
    logger.info(f"- Node address: {NODE_IP}:{NODE_PORT}")
    logger.info(f"- Database file: {DATABASE_FILE}")
    logger.info(f"- Qtry path: {QUOTTERY_LIBS}")

    # Check if the qtry wrapper exists and init the qtry wrapper
    if not os.path.isfile(QUOTTERY_LIBS):
        logger.info(f"quottery_cpp_wrapper path NOT FOUND: {QUOTTERY_LIBS}. Exiting.")
        sys.exit(1)
    qt = quottery_cpp_wrapper.QuotteryCppWrapper(QUOTTERY_LIBS, NODE_IP, NODE_PORT, 'DB_UPDATER')

    init_db()
    update_database_with_active_bets()
