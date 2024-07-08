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

PAGINATIONS_FILTER = [
    "bet_id",
    "close_date",
    "creator",
    "end_date",
    "max_slot_per_option",
    "no_ops",
    "no_options",
    "open_date",
    "option_desc",
    "result",
    "status",
    # list
    "oracle_id",
    "bet_desc"
]

def filter_pagination(bets_list):
    filtered_bets = bets_list
    for pagin in PAGINATIONS_FILTER:
        pagin_filter = request.args.get(pagin)
        if pagin_filter:
            # This only check for containing
            if pagin == 'bet_desc' or pagin == 'oracle_id':
                filtered_bets = list(filter(lambda p: pagin_filter in p[pagin], filtered_bets))
            else: # Check for match all
                filtered_bets = list(filter(lambda p: str(p[pagin]) == pagin_filter, filtered_bets))
    return filtered_bets

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

    filtered_bets = filter_pagination(bets_list)

    ret = {
        'bet_list': filtered_bets,
        'node_info': node_info,
        'paginations' : PAGINATIONS_FILTER
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
