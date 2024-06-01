import os
import sqlite3
import requests
from flask_cors import CORS
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

CPP_SERVER_URL = 'http://192.168.1.212:6000'


def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quottery_info (
            bet_id INTEGER PRIMARY KEY,
            no_options INTEGER NOT NULL,
            creator TEXT NOT NULL,
            bet_desc TEXT NOT NULL,
            option_desc TEXT NOT NULL,
            max_slot_per_option INTEGER NOT NULL,
            amount_per_bet_slot REAL NOT NULL,
            open_date TEXT,
            close_date TEXT,
            end_date TEXT,
            result INTEGER,
            no_ops INTEGER,
            oracle_id TEXT,
            oracle_fee TEXT,
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


def fetch_active_bets_from_cpp_server():
    try:
        cpp_response = requests.get(os.path.join(CPP_SERVER_URL, 'get_active_bets'))
        cpp_response.raise_for_status()
        return cpp_response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to communicate with C++ server: {e}")
        return []


def update_database_with_active_bets(active_bets):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch current active bets in the database
    cursor.execute('SELECT bet_id FROM quottery_info')
    current_bet_ids = {row[0] for row in cursor.fetchall()}

    # Add new bets and update existing ones
    new_bet_ids = set()
    for active_bet in active_bets:
        new_bet_ids.add(active_bet['bet_id'])

        if active_bet['bet_id'] not in current_bet_ids:
            cursor.execute('''
                INSERT INTO quottery_info (bet_id, no_options, creator, bet_desc, option_desc, max_slot_per_option, amount_per_bet_slot, open_date, close_date, end_date, result, no_ops, oracle_id, oracle_fee, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                active_bet['bet_id'],
                active_bet['no_options'],
                active_bet['creator'],
                active_bet['bet_desc'],
                active_bet['option_desc'],
                active_bet['max_slot_per_option'],
                active_bet['amount_per_bet_slot'],
                active_bet['open_date'],
                active_bet['close_date'],
                active_bet['end_date'],
                active_bet['result'],
                active_bet['no_ops'],
                active_bet['oracle_id'],
                active_bet['oracle_fee'],
                active_bet['status'],))

    # Remove bets that are no longer active
    active_bet_ids = {bet['bet_id'] for bet in active_bets}
    bets_to_inactive = active_bet_ids - (current_bet_ids.union(new_bet_ids))
    for bet_id in bets_to_inactive:
        cursor.execute('UPDATE quottery_info SET status = 0 WHERE bet_id = ?', (bet_id,))

    conn.commit()
    conn.close()


@app.route('/get_active_bets', methods=['GET'])
def get_active_bets():
    # Assuming this is the part to load from the C++ server, comment for now
    # [TODO]:
    #  1. Load from C++ server
    #  2. Update the database
    #  3. Load from the database

    # Fetch active bets from the C++ server
    # active_bets = fetch_active_bets_from_cpp_server()

    # Update the SQLite database with the newest active bets
    # update_database_with_active_bets(active_bets)

    # Load the updated bet list from the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM quottery_info')
    bets = cursor.fetchall()
    conn.close()

    bets_list = []
    for bet in bets:
        bets_list.append({
            'bet_id': bet[0],
            'no_options': bet[1],
            'creator': bet[2],
            'bet_desc': bet[3],
            'option_desc': bet[4],
            'max_slot_per_option': bet[5],
            'amount_per_bet_slot': bet[6],
            'open_date': bet[7],
            'close_date': bet[8],
            'end_date': bet[9],
            'result': bet[10],
            'no_ops': bet[11],
            'oracle_id': bet[12],
            'oracle_fee': bet[13],
            'status': bet[14],
        })

    return jsonify(bets_list)


@app.route('/join_bet', methods=['POST'])
def join_bet():
    data = request.json

    # Send JSON to C++ server
    # try:
    #     cpp_response = requests.post(os.path.join(CPP_SERVER_URL, 'join_bet'), json=data)
    #     cpp_response.raise_for_status()
    # except requests.exceptions.RequestException as e:
    #     return jsonify({"error": "Failed to communicate with C++ server", "message": str(e)}), 500
    #
    # if cpp_response.status_code != 201:
    #     return jsonify({"error": "C++ server failed to create bet", "message": cpp_response.text}), 500

    conn = sqlite3.connect('database.db')
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

    return jsonify({"message": "Bet joined successfully!"}), 201


@app.route('/add_bet', methods=['POST'])
def add_bet():
    data = request.json

    # Send JSON to C++ server
    # try:
    #     cpp_response = requests.post(os.path.join(CPP_SERVER_URL, 'add_bet'), json=data)
    #     cpp_response.raise_for_status()
    # except requests.exceptions.RequestException as e:
    #     return jsonify({"error": "Failed to communicate with C++ server", "message": str(e)}), 500
    #
    # if cpp_response.status_code != 201:
    #     return jsonify({"error": "C++ server failed to create bet", "message": cpp_response.text}), 500

    # Fetch active bets from C++ server to update the database
    # bets = fetch_active_bets_from_cpp_server()
    # update_database_with_active_bets(bets)
    ##### [Remove later] The above is replaced by the update directly to the database, skipping C++ server fetching for now
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bet_id FROM quottery_info ORDER BY bet_id DESC LIMIT 1;')
    latest_bet_id = cursor.fetchall()[0][0]
    print(latest_bet_id)
    cursor.execute('''
                INSERT INTO quottery_info (bet_id, no_options, creator, bet_desc, option_desc, max_slot_per_option, amount_per_bet_slot, open_date, close_date, end_date, result, no_ops, oracle_id, oracle_fee, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
        latest_bet_id + 1,
        data['no_options'],
        data['creator'],
        data['bet_desc'],
        ','.join(data['option_desc']),
        data['max_slot_per_option'],
        data['amount_per_bet_slot'],
        data['open_date'],
        data['close_date'],
        data['end_date'],
        data['result'],
        data['no_ops'],
        ','.join(data['oracle_id']),
        ','.join(data['oracle_fee']),
        data['status'],))
    conn.commit()
    conn.close()
    ##### [End of Remove later]

    # Load the updated bet list from the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM quottery_info ORDER BY bet_id DESC LIMIT 1;')
    db_latest_bet = cursor.fetchall()
    conn.close()

    # Double check
    new_bet_id = None
    for bet in db_latest_bet:
        if bet[3] == data['bet_desc'] and \
                bet[2] == data['creator'] and \
                bet[1] == data['no_options']:
            new_bet_id = bet[0]
            break

    if new_bet_id:
        return jsonify({"message": "Bet added successfully!", "bet_id": new_bet_id}), 201
    else:
        return jsonify({"error": "Failed to find the newly created bet in the active list"}), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
