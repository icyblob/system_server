import os
import sqlite3
import json
import quottery_cpp_wrapper
from flask_cors import CORS
from flask import Flask, request, jsonify

app = Flask(__name__)
CORS(app)

# IP to a active node
NODE_IP = '192.168.1.10'
NODE_PORT = 12345

QUOTTERY_LIBS = 'libs/quottery_cpp/lib/libquottery_cpp.so'
qt = quottery_cpp_wrapper.QuotteryCppWrapper(QUOTTERY_LIBS, NODE_IP, NODE_PORT)

DATABASE_FILE = 'database.db'

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
            current_bet_state TEXT NOT NULL,
            max_slot_per_option INTEGER NOT NULL,
            min_bet_amount REAL NOT NULL,
            open_date TEXT,
            close_date TEXT,
            end_date TEXT,
            result INTEGER,
            no_ops INTEGER,
            oracle_id TEXT,
            oracle_fee REAL NOT NULL,
            status INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_bet_info (
            user_bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bet_id INTEGER NOT NULL,
            user_id TEXT NOT NULL ,
            option_id INTEGER NOT NULL,
            num_slots INTEGER NOT NULL,
            amount_per_slot REAL NOT NULL,
            FOREIGN KEY (bet_id) REFERENCES quottery_info(bet_id)
        )
    ''')
    conn.commit()
    conn.close()


def fetch_active_bets_from_node():
    # Connect to the node and get current active bets
    # TODO: Process the disconnected issue
    active_bets = qt.get_active_bets()
    return active_bets


def submit_join_bet(betInfo):
    tx_hash, tx_tick = qt.join_bet(betInfo)
    return (tx_hash, tx_tick)


def submit_add_bet(betInfo):
    tx_hash, tx_tick = qt.add_bet(betInfo)
    return (tx_hash, tx_tick)

def update_database_with_active_bets():

    # Fetch active bets from the nodes
    active_bets = fetch_active_bets_from_node()

    # Verify the active_bets
    if len(active_bets) == 0:
        print('[WARNING] Active bets from node is empty! Display the local database')

    # Connect to the database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Update the database
    # TODO: Verify the existed one ? Or just update the newest one that is verified from node
    new_bet_ids = []
    for key, active_bet in active_bets.items():
        cursor.execute('''
        INSERT OR REPLACE INTO quottery_info (bet_id, no_options, creator, bet_desc, option_desc, current_bet_state, max_slot_per_option, min_bet_amount, open_date, close_date, end_date, result, no_ops, oracle_id, oracle_fee, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
            active_bet['bet_id'],
            active_bet['no_options'],
            active_bet['creator'],
            active_bet['bet_desc'],
            json.dumps(active_bet['option_desc']), # This should be a separate table
            json.dumps(active_bet['current_bet_state']), # This should be a separate table
            active_bet['max_slot_per_option'],
            active_bet['min_bet_amount'],
            active_bet['open_date'],
            active_bet['close_date'],
            active_bet['end_date'],
            active_bet['result'],
            active_bet['no_ops'],
            json.dumps(active_bet['oracle_id']), # This should be a separate table
            json.dumps(active_bet['oracle_fee']), # This should be a separate table
            active_bet['status']
        ))
        new_bet_ids.append(key)

    # Mark the old bet status as 0
    update_statement = 'UPDATE quottery_info SET status = 0 WHERE bet_id NOT IN ({});'.format(
    ','.join('?' for _ in new_bet_ids))
    cursor.execute(update_statement, new_bet_ids)

    conn.commit()
    conn.close()


@app.route('/get_active_bets', methods=['GET'])
def get_active_bets():
    # Fetch data and update the SQLite database with the newest active bets
    update_database_with_active_bets()

    # Load the updated bet list from the updated SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM quottery_info')
    rows = cursor.fetchall()
    conn.close()

    # Convert rows to a list of dictionaries
    bets_list = [dict(row) for row in rows]

    # Reply with json
    return jsonify(bets_list)


@app.route('/join_bet', methods=['POST'])
def join_bet():

    # Get data from request
    data = request.json

    # Request join bet to the node
    tx_hash, tx_tick = submit_join_bet(data)

    # Join bet will need to wait for a few sticks to make sure it appears
    # So we can not check here. May be notify wait for some sticks ?

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO user_bet_info (bet_id, user_id, option_id, num_slots, amount_per_slot)
            VALUES (?, ?, ?, ?, ?) ''', (
        data['bet_id'],
        data['user_id'],
        data['option_id'],
        data['num_slots'],
        data['amount_per_slot']
    ))
    conn.commit()
    conn.close()

    if tx_tick > 0:
        message = 'Bet joined successfully.'
        message = message + 'TxTick: ' + str(tx_tick)
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
        message = message + 'TxTick: ' + str(tx_tick)
        message = message + ', TxHash: ' + tx_hash
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": "Failed to submit the bet"}), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
