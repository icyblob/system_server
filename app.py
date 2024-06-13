import os
import sqlite3
import json
import quottery_cpp_wrapper
from flask_cors import CORS
from flask import Flask, request, jsonify

app = Flask(__name__)
CORS(app)

# IP to a active node
NODE_IP = '5.199.134.150'
NODE_PORT = 31844

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
            current_bet_state TEXT,
            max_slot_per_option INTEGER NOT NULL,
            amount_per_bet_slot REAL NOT NULL,
            open_date TEXT,
            close_date TEXT,
            end_date TEXT,
            result INTEGER,
            no_ops INTEGER,
            oracle_id TEXT,
            oracle_fee REAL,
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
            user_id TEXT NOT NULL ,
            option_id INTEGER NOT NULL,
            num_slots INTEGER NOT NULL,
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


def update_database_with_active_bets():

    # Fetch active bets from the nodes
    active_bets = fetch_active_bets_from_node()

    # Verify the active_bets
    if len(active_bets) == 0:
        print('[WARNING] Active bets from node is empty! Display the local database')

    # Connect to the database
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
        active_bet_ids.append(active_bet['bet_id'])
        if check_primary_key_exists(cursor=cursor, table_name='quottery_info',
                                 primary_key_column='bet_id',
                                 primary_key_value=active_bet['bet_id']) is False:
            cursor.execute('''
                INSERT INTO quottery_info (bet_id, no_options,  creator,  bet_desc,  option_desc, current_bet_state,  max_slot_per_option,  amount_per_bet_slot,  open_date,  close_date,  end_date,  result,  no_ops,  oracle_id,  oracle_fee,  status, current_num_selection, current_total_qus, betting_odds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                active_bet['bet_id'],
                active_bet['no_options'],
                active_bet['creator'],
                active_bet['bet_desc'],
                json.dumps(active_bet['option_desc']),  # This should be a separate table
                json.dumps(active_bet['current_bet_state']),
                active_bet['max_slot_per_option'],
                active_bet['min_bet_amount'],
                active_bet['open_date'],
                active_bet['close_date'],
                active_bet['end_date'],
                active_bet['result'],
                active_bet['no_ops'],
                json.dumps(active_bet['oracle_id']), # This should be a separate table
                json.dumps(active_bet['oracle_fee']), # This should be a separate table
                1,
                json.dumps(['0'] * active_bet['no_options']),
                '0',
                json.dumps(['1'] * active_bet['no_options']),
            ))

    inactive_bet_ids = set(db_bet_ids) - set(active_bet_ids)

    # Mark the old bet status as 0
    update_statement = 'UPDATE quottery_info SET status = 0 WHERE bet_id IN ({});'.format(
        ','.join('?' for _ in inactive_bet_ids))
    cursor.execute(update_statement, list(inactive_bet_ids))

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

    # Hot fix for current_num_selection. Will remove using current_num_selection
    for i, bl in enumerate(bets_list):
        for key in bl:
            if key == 'current_num_selection':
                print(bl[key])
                try:
                    _ = json.loads(bl[key])
                except:
                    bets_list[i][key] = json.dumps(bl[key].split(','))

    # Reply with json
    return jsonify(bets_list)


def create_trigger(conn):
    cursor = conn.cursor()
    cursor.execute('''
        -- Create trigger to update current_num_selection and current_total_qus
        CREATE TRIGGER IF NOT EXISTS after_insert_user_bet_info
        AFTER INSERT ON user_bet_info
        FOR EACH ROW
        BEGIN
            -- Update current_total_qus
            UPDATE quottery_info
            SET current_total_qus = (
                SELECT COALESCE(SUM(num_slots * amount_per_slot), 0)
                FROM user_bet_info
                WHERE bet_id = NEW.bet_id
            )
            WHERE bet_id = NEW.bet_id;
        
            -- Update current_num_selection
            UPDATE quottery_info
            SET current_num_selection = (
                WITH RECURSIVE generate_options(option_id) AS (
                    SELECT 0 AS option_id
                    UNION ALL
                    SELECT option_id + 1
                    FROM generate_options
                    WHERE option_id + 1 < (SELECT no_options FROM quottery_info WHERE bet_id = NEW.bet_id)
                ),
                option_counts AS (
                    SELECT 
                        option_id, 
                        SUM(num_slots) AS num_slots
                    FROM 
                        user_bet_info
                    WHERE bet_id = NEW.bet_id
                    GROUP BY 
                        option_id
                ),
                filled_options AS (
                    SELECT 
                        generate_options.option_id,
                        COALESCE(option_counts.num_slots, 0) AS num_slots
                    FROM 
                        generate_options
                    LEFT JOIN 
                        option_counts
                    ON 
                        generate_options.option_id = option_counts.option_id
                )
                SELECT 
                    GROUP_CONCAT(num_slots, ',')
                FROM 
                    filled_options
            )
            WHERE bet_id = NEW.bet_id;
        END;
    ''')
    conn.commit()


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


def update_betting_odds(conn, bet_id):
    # Retrieve current_num_selection for the given bet_id
    cur = conn.cursor()
    cur.execute("SELECT current_num_selection FROM quottery_info WHERE bet_id = ?", (bet_id,))
    row = cur.fetchone()

    if row:
        current_num_selection = list(map(int, row[0].split(',')))
        total_selections = sum(current_num_selection)

        # Calculate betting odds
        if total_selections == 0:
            betting_odds = [1] * len(current_num_selection)
        else:
            betting_odds = [total_selections / selection if selection > 0 else total_selections for selection in current_num_selection]

        betting_odds = [f'"{e}"' for e in betting_odds]
        betting_odds_str = "[" + ','.join(betting_odds) + "]"

        # Update the betting_odds in the database
        cur.execute("UPDATE quottery_info SET betting_odds = ? WHERE bet_id = ?", (betting_odds_str, bet_id))
        print(f"Betting odds updated for bet_id {bet_id}")
    else:
        print(f"No entry found for bet_id {bet_id}")


@app.route('/join_bet', methods=['POST'])
def join_bet():

    # Get data from request
    data = request.json

    # Request join bet to the node
    tx_hash, tx_tick = submit_join_bet(data)

    # Join bet will need to wait for a few sticks to make sure it appears
    # So we can not check here. May be notify wait for some sticks ?

    conn = sqlite3.connect(DATABASE_FILE)
    create_trigger(conn)
    insert_user_bet_info(conn, data)
    update_betting_odds(conn, data['bet_id'])
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
