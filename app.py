import os
import sys
import sqlite3
import json
import quottery_cpp_wrapper
from flask_cors import CORS
from flask import Flask, request, jsonify
from threading import Thread
import time
from datetime import datetime, timezone
import argparse

app = Flask(__name__)
CORS(app)

DEBUG_MODE = False
# IP to an active node
DEFAULT_NODE_IP = '5.199.134.150'
DEFAULT_NODE_PORT = 31844

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
        print(f"Error get active basic info of qtry from node: {e}")
        return 1, {}

def fetch_active_bets_from_node():
    # Connect to the node and get current active bets
    try:
        sts, active_bets = qt.get_active_bets()
        return (sts, active_bets)
    except Exception as e:
        print(f"Error fetching active bets from node: {e}")
        return (1, {})


def get_bet_info_from_node(betId):
    try:
        sts, betInfo = qt.get_bet_info(betId)
        return (sts, betInfo)
    except Exception as e:
        print(f"Error fetching active bets from node: {e}")
        return 1, {}


def submit_join_bet(betInfo):
    try:
        tx_hash, tx_tick = qt.join_bet(betInfo)
        return (tx_hash, tx_tick)
    except Exception as e:
        print(f"Error submitting join bet: {e}")
        return (None, -1)


def submit_add_bet(betInfo):
    try:
        tx_hash, tx_tick = qt.add_bet(betInfo)
        return (tx_hash, tx_tick)
    except Exception as e:
        print(f"Error submitting add bet: {e}")
        return (None, -1)


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
                print('[WARNING] Active bets from node is empty! Display the local database')

            sts, qt_basic_info = get_qtry_basic_info_from_node()
            if not qt_basic_info:
                print('[WARNING] Basic info from node is empty!')
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
           print(f"Error updating database: {e}")
        finally:
            time.sleep(UPDATE_INTERVAL)  # Wait for 3 seconds before the next update


@app.route('/get_active_bets', methods=['GET'])
def get_active_bets():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM quottery_info')
    rows = cursor.fetchall()
    conn.close()

    # Convert rows to a list of dictionaries
    bets_list = [dict(row) for row in rows]

    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM node_basic_info')
    node_basic_info_rows = cursor.fetchall()
    conn.close()

    node_info = [dict(row) for row in node_basic_info_rows]

    ret = {
        'bet_list': bets_list,
        'node_info': node_info
    }

    # Reply with json
    return jsonify(ret)


def insert_user_bet_info(conn, data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_bet_info (bet_id, user_id, option_id, num_slots, amount_per_slot)
            VALUES (?, ?, ?, ?, ?) ''', (
        data['bet_id'],
        "None",
        data['option_id'],
        data['num_slots'],
        data['amount_per_slot']
    ))
    conn.commit()
    update_current_total_qus(conn, data['bet_id'])
    conn.commit()


@app.route('/join_bet', methods=['POST'])
def join_bet():
    # Get data from request
    data = request.json

    # Request join bet to the node
    tx_hash, tx_tick = submit_join_bet(data)

    # Join bet will need to wait for a few sticks to make sure it appears
    # So we can not check here. May be notify wait for some sticks ?

    conn = sqlite3.connect(DATABASE_FILE)
    insert_user_bet_info(conn, data)
    update_betting_odds(conn, data['bet_id'])
    conn.commit()
    conn.close()

    if tx_tick > 0:
        message = 'Bet joined successfully.'
        message = message + ' TxTick: ' + str(tx_tick)
        message = message + ', TxHash: ' + tx_hash
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": "Failed to submit the bet"}), 500


@app.route('/add_bet', methods=['POST'])
def add_bet():
    # Get the request
    data = request.json

    # Submit adding bet to node
    tx_hash, tx_tick = submit_add_bet(data)

    # Because adding bet will need to wait for a few sticks to make sure it appears
    # So we can not check here. May be notify wait for some sticks ?
    if tx_tick > 0:
        message = 'Bet submitted successfully! '
        message = message + ' TxTick: ' + str(tx_tick)
        message = message + ', TxHash: ' + tx_hash
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": "Failed to submit the bet"}), 500


if __name__ == '__main__':
    # Create the parser
    parser = argparse.ArgumentParser(description='System server for qtry.')

    # Arguments
    parser.add_argument('-appport', type=int, default=5000, help='The port of this app')
    parser.add_argument('-nodeip', type=str, default=DEFAULT_NODE_IP, help='Node IP address')
    parser.add_argument('-nodeport', type=int, default=DEFAULT_NODE_PORT, help='Node port number')
    parser.add_argument('-dbpath', type=str, default='.', help='Directory contain the database file')
    parser.add_argument('-debug', action='store_true', help='Enable debug mode (default: False)')

    # Execute the parse_args() method
    args = parser.parse_args()

    # Access the arguments
    DEBUG_MODE = args.debug
    APP_PORT = args.appport
    NODE_IP = args.nodeip
    NODE_PORT = args.nodeport
    DATABASE_PATH = args.dbpath
    DATABASE_FILE = os.path.join(DATABASE_PATH, DATABASE_FILE)
    print("Launch the app with configurations")
    print(f"- App port: {APP_PORT}")
    print(f"- Node address: {NODE_IP}:{NODE_PORT}")
    print(f"- Database file: {DATABASE_FILE}")
    print(f"- Qtry path: {QUOTTERY_LIBS}")
    print(f"- Debug mode: {DEBUG_MODE}")

    # Check if the qtry wrapper exists and init the qtry wrapper
    if not os.path.isfile(QUOTTERY_LIBS):
        print(f"quottery_cpp_wrapper path NOT FOUND: {QUOTTERY_LIBS}. Exiting.")
        sys.exit(1)
    qt = quottery_cpp_wrapper.QuotteryCppWrapper(QUOTTERY_LIBS, NODE_IP, NODE_PORT)

    init_db()
    update_quottery_info_thread = Thread(target=update_database_with_active_bets)
    update_quottery_info_thread.daemon = True
    update_quottery_info_thread.start()

    # Insert the ssl crt and key here
    ssl_context = (os.getenv('CERT_PATH'), os.getenv('CERT_KEY_PATH'))
    if DEBUG_MODE:
        ssl_context = 'adhoc'

    app.run(host='0.0.0.0', port=APP_PORT, debug=DEBUG_MODE, ssl_context=ssl_context)
