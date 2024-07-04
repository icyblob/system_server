import os
import sys
import sqlite3
import json
from flask_cors import CORS
from flask import Flask, request, jsonify
import time
from datetime import datetime, timezone
import logging

log_format = '[%(name)s][%(asctime)s] %(message)s'
# Configure the logging module to use the custom format
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger('FLASK')

app = Flask(__name__)
CORS(app)

# Init default parameters
DEBUG_MODE = False
APP_PORT = 5000
NODE_IP = None
NODE_PORT = None
DATABASE_PATH = "."
DATABASE_FILE = 'database.db'

@app.route('/get_bets', methods=['GET'])
def get_bets():

    if not os.path.isfile(DATABASE_FILE):
        logger.warning(f"No database find ${DATABASE_FILE}. Please wait...")
        return jsonify({'bet_list': [], 'node_info': []})

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

@app.route('/get_active_bets', methods=['GET'])
def get_active_bets():

    if not os.path.isfile(DATABASE_FILE):
        logger.warning(f"No database find ${DATABASE_FILE}. Please wait...")
        return jsonify({'bet_list': [], 'node_info': []})

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

    # Active bet is the bet that doesn't have the result
    filtered_bets = bets_list
    filtered_bets = list(filter(lambda p: p['result'] < 0, filtered_bets))

    # Check the closed date and close time
    current_utc_date = datetime.now(timezone.utc)
    active_bets = []
    for bet in filtered_bets:
        active_flag = True
        # Combine the date and time strings and parse them into a datetime object
        closed_datetime_str = bet['close_date'] + ' ' + bet['close_time']
        try:
            closed_datetime = datetime.strptime(closed_datetime_str, '%y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            active_flag = closed_datetime > current_utc_date
        except Exception as e:
            logger.warning(f"Date time format is not correct. Will not use for filtering active/inactive: {e}")

        if active_flag:
            active_bets.append(bet)


    ret = {
        'bet_list': active_bets,
        'node_info': node_info
    }

    # Reply with json
    return jsonify(ret)

if __name__ == '__main__':
    # Init parameters with environment variables
    if os.getenv('DEBUG_MODE'):
        DEBUG_MODE = os.getenv('DEBUG_MODE')

    if os.getenv('APP_PORT'):
        APP_PORT = os.getenv('APP_PORT')

    if os.getenv('DATABASE_PATH'):
        DATABASE_PATH = os.getenv('DATABASE_PATH')

    DATABASE_FILE = os.path.join(DATABASE_PATH, DATABASE_FILE)

    # Print the configuration to verify
    logger.info("Launch the flask app with configurations")
    logger.info(f"- App port: {APP_PORT}")
    logger.info(f"- Database read location: {DATABASE_FILE}")
    logger.info(f"- Debug mode: {DEBUG_MODE}")

    # Insert the ssl crt and key here
    ssl_context = (os.getenv('CERT_PATH'), os.getenv('CERT_KEY_PATH'))
    if DEBUG_MODE:
        ssl_context = 'adhoc'

    app.run(host='0.0.0.0', threaded=True ,port=APP_PORT, debug=DEBUG_MODE, ssl_context=ssl_context)
