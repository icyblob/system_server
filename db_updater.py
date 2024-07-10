import os
import sys
import sqlite3
import json
import quottery_cpp_wrapper
from threading import Thread
import time
from datetime import datetime, timezone
import argparse
from packaging.version import parse as parse_version
import shutil
import logging

log_format = '[%(name)s][%(asctime)s] %(message)s'
# Configure the logging module to use the custom format
logging.basicConfig(level=logging.INFO, format=log_format)

# Example usage of the logger
logger = logging.getLogger('DB_UPDATER')

# Init default parameters
# DB version
DB_VERSION = "2.1"
NODE_IP = None
NODE_PORT = None
DATABASE_PATH = "."

QUOTTERY_LIBS = 'libs/quottery_cpp/lib/libquottery_cpp.so'
qt = None

DATABASE_FILE = 'database.db'
UPDATE_INTERVAL = 3  # seconds

def init_tick_info():
    # Connect to your SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Update the bet detail option table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tick_info (
            tick_number INTEGER,
            epoch INTEGER,
            tick_duration INTEGER,
            number_of_aligned_votes INTEGER,
            number_of_misaligned_votes INTEGER,
            initial_tick INTEGER,
            PRIMARY KEY (tick_number, epoch)   
            )  
            ''')
    # Check if the row exists
    cursor.execute("SELECT COUNT(*) FROM tick_info")
    row_count = cursor.fetchone()[0]

    if row_count == 0:
        cursor.execute(
            f'''INSERT INTO tick_info 
            (tick_number, epoch, tick_duration, number_of_aligned_votes, number_of_misaligned_votes, initial_tick) 
            VALUES  
            (0, 0, 0, 0, 0, 0)''')
    else:
        cursor.execute(f'''UPDATE tick_info SET tick_number = 0''')
        cursor.execute(f'''UPDATE tick_info SET epoch = 0''')
        cursor.execute(f'''UPDATE tick_info SET tick_duration = 0''')
        cursor.execute(f'''UPDATE tick_info SET number_of_aligned_votes = 0''')
        cursor.execute(f'''UPDATE tick_info SET number_of_misaligned_votes = 0''')
        cursor.execute(f'''UPDATE tick_info SET initial_tick = 0''')

    conn.commit()
    conn.close()

def init_node_basic_info():
    # Connect to your SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_basic_info (
            ip TEXT,
            port INTEGER,
            fee_per_slot_per_hour INTEGER,
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

    # There is an existed node ip. Remove it to make sure doesn't conflict with current node ip and port
    cursor.execute(f'''DELETE FROM node_basic_info''')
        
    conn.commit()
    conn.close()

# Create db file
def create_db_file():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS version (
            version_info TEXT PRIMARY KEY)'''
    )
    # Insert or update the version information
    cursor.execute('''
    INSERT INTO version (version_info) VALUES (?);
    ''', (DB_VERSION,))

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

    # Update the bet detail option table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bet_options_detail (
            bet_id INTEGER,
            option_id INTEGER,
            user_slots TEXT,
            PRIMARY KEY (bet_id, option_id)
            )''')

    conn.commit()
    conn.close()

    init_tick_info()

# Update from unversion to 1.0
def update_db_unversion_to_1_0():
    update_version = "1.0"

    # Connect to your SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Create a table for versioning if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS version (
            version_info TEXT PRIMARY KEY)''')

    # Insert or update the version information
    cursor.execute('''
    INSERT INTO version (version_info) VALUES (?);
    ''', (update_version,))

    # Rename the fee per day to fee per house. Also this will invalidate the fee per day
    cursor.execute(f"ALTER TABLE node_basic_info RENAME COLUMN fee_per_slot_per_day TO fee_per_slot_per_hour ;")
    # Mark the values in 'fee_per_slot_per_hour' as invalid
    cursor.execute('''
        UPDATE node_basic_info SET fee_per_slot_per_hour = 0;
    ''')

    conn.commit()
    conn.close()

# Update from 1.0 to 2.0
def update_db_1_0_to_2_0():
    update_version = "2.0"

    # Connect to your SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Insert or update the version information
    cursor.execute('''
    UPDATE version SET version_info = ?;
    ''', (update_version,))

    # Update the bet detail option table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bet_options_detail (
            bet_id INTEGER,
            option_id INTEGER,
            user_slots TEXT,
            PRIMARY KEY (bet_id, option_id)
            )''')

    conn.commit()
    conn.close()

# Update from 2.0 to 2.1
def update_db_2_0_to_2_1():
    update_version = "2.1"

    # Connect to your SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Insert or update the version information
    cursor.execute('''
    UPDATE version SET version_info = ?;
    ''', (update_version,))

    conn.commit()
    conn.close()

    init_tick_info()

def backup_db(version):
    # Back up the database file
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    # New file name with the timestamp
    backupfile = f"{DATABASE_FILE.split('.')[0]}_v{version}_bk_{timestamp}.db"
    # Copy the original file to the new file
    logger.info(f"Backing up db file into {backupfile}")
    shutil.copyfile(DATABASE_FILE, backupfile)

# Function that check if we need to convert the old version to new version of table
# Only have ability update version gradually. Can not jump from a very old version
def update_db():
    # Check the existed db with current db in code
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    version_info = "unversion"

    # Check if a version table exists
    table_name = 'version'
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    table_exists = cursor.fetchone() is not None
    need_update = not table_exists

    field_exists = False;
    if table_exists:
        field_name = 'version_info'
        cursor.execute(f"PRAGMA table_info({table_name});")
        fields = [info[1] for info in cursor.fetchall()]
        field_exists = field_name in fields
        if field_exists:
            cursor.execute('SELECT version_info FROM version;')
            # Fetch the result
            version_info = cursor.fetchone()[0]
            if parse_version(DB_VERSION) == parse_version(version_info):
                need_update = False
            else:
                need_update = True
        else:
            need_update = True
    conn.close()

    if need_update:
        logger.info(f"Version is mismatched current: %s vs supported: %s", version_info, DB_VERSION)

        # Update from unversion to 1.0
        if not field_exists:
            logger.info(f"Updating db from unversion to 1.0 ...")

            # Back up the database file
            backup_db("00")

            # Update the file
            update_db_unversion_to_1_0()
            version_info = "1.0"

            logger.info(f"Updated db version to %s", version_info)

        # Update from other version happend sequential here if neccessary
        if parse_version(version_info) < parse_version("2.0"):
            logger.info(f"Updating db from {version_info}  to 2.0 ...")
            # Back up the database file
            backup_db("10")

            # Update the file
            update_db_1_0_to_2_0()
            version_info = "2.0"
            logger.info(f"Finished update db version to %s", version_info)

        if parse_version(version_info) < parse_version("2.1"):
            logger.info(f"Updating db from {version_info} to 2.1 ...")

            # Back up the database file
            backup_db("20")
            update_db_2_0_to_2_1()
            version_info = "2.1"
            logger.info(f"Finished update db version to %s", version_info)

        if parse_version(version_info) != parse_version(DB_VERSION):
            logger.error(f"Can not update from db from %s to %s", version_info, DB_VERSION)
            sys.exit(1)

        logger.info(f"Update db version successfully. Current version {DB_VERSION}")
    else:
        logger.info(f"Version is matched. Skip the update.")


def init_db():
    if os.path.exists(DATABASE_FILE):
        logger.info("Database file found. Checking version and update if neccessary.")
        update_db()
    else:
        logger.info("No database file found. Create a new one.")
        create_db_file()

    # Node basic information will depend on the node it connect to
    # So it is better to clean it up to not mess up when we change the node
    init_node_basic_info()

def get_qtry_basic_info_from_node():
    # Connect to the node and get current basic info of qtry
    try:
        sts, qtry_basic_info = qt.get_qtry_basic_info()
        return (sts, qtry_basic_info)
    except Exception as e:
        logger.warning(f"Error get active basic info of qtry from node: {e}")
        return 1, {}

def fetch_bets_from_node():
    # Connect to the node and get all bets
    try:
        sts, all_bets, tick_number = qt.get_all_bets()
        return (sts, all_bets, tick_number)
    except Exception as e:
        logger.warning(f"Error fetching all bets from node: {e}")
        return (1, {}, 0)

def get_bet_info_from_node(betId):
    try:
        sts, betInfo = qt.get_bet_info(betId)
        return (sts, betInfo)
    except Exception as e:
        logger.warning(f"Error fetching bet info from node: {e}")
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
    """ Update total of qus betting into database """

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
    """ Update betting odds into database """
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


def update_database_with_bets():
    """ Fetch all bet data related from node and update the database """
    while True:
        try:
            logger.info("Requesting data from node.")
            sts, all_bets, tick_number = fetch_bets_from_node()

            # Update the tick table
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            # Fetch current tick in db
            cursor.execute('''
                SELECT tick_number
                FROM tick_info
            ''')
            table_tick_number = cursor.fetchone()[0]
            # Update tick number with the latest
            tick_number = max(tick_number, table_tick_number)
            cursor.execute(f'''UPDATE tick_info SET tick_number = {tick_number}''')
            conn.commit()
            conn.close()

            # Verify the bets
            if not all_bets:
                logger.warning('[WARNING] Bets from node is empty! Using the local database')

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
                        fee_per_slot_per_hour,
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
                    qt_basic_info['fee_per_slot_per_hour'],
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
            for key, active_bet in all_bets.items():
                active_bet_ids.append(key)
                # Update the database if the bet info is valid
                if active_bet:
                    # Check the bet from node is inactive
                    ## Result checking
                    bet_status = 1
                    if active_bet['result'] >= 0:
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

                    # Bet detail options
                    number_of_options = active_bet['no_options']
                    for op_id in range(0, number_of_options):
                        sts, bet_option_detail = qt.get_bet_option_detail(active_bet['bet_id'], op_id)
                        if bet_option_detail :
                            #logger.info(f'Bet detail of bet %d options %d', active_bet['bet_id'], op_id)
                            #logger.info(bet_option_detail)
                            cursor.execute(f'''
                                INSERT OR REPLACE INTO bet_options_detail (
                                    bet_id,
                                    option_id,
                                    user_slots)
                                VALUES (?, ?, ?)
                                ''', (
                                active_bet['bet_id'],
                                op_id,
                                json.dumps(bet_option_detail)
                            ))

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
    update_database_with_bets()
