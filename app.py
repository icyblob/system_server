import os
import logging
import sqlite3

from flask_cors import CORS
from flask import Flask, jsonify
from datetime import datetime, timezone

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


def get_bets_base():
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

    return bets_list, node_info


def filter_active_bets(bets_list):
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
            active_flag = current_utc_date < closed_datetime
        except Exception as e:
            logger.warning(f"Date time format is not correct. Will not use for filtering active/inactive: {e}")

        if active_flag:
            active_bets.append(bet)

    return active_bets


def filter_locked_bets(bets_list):
    # Check the closed/end date and close/end time
    current_utc_date = datetime.now(timezone.utc)
    locked_bets = []
    for bet in bets_list:
        locked_flag = True
        closed_datetime_str = bet['close_date'] + ' ' + bet['close_time']
        end_datetime_str = bet['end_date'] + ' ' + bet['end_time']

        try:
            closed_datetime = datetime.strptime(closed_datetime_str, '%y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            end_datetime = datetime.strptime(end_datetime_str, '%y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            locked_flag = closed_datetime <= current_utc_date < end_datetime
        except Exception as e:
            logger.warning(f"Date time format is not correct. Will not use for filtering active/inactive: {e}")

        if locked_flag:
            locked_bets.append(bet)

    return locked_bets


def filter_inactive_bets(bets_list):
    # Check the end date and close time
    current_utc_date = datetime.now(timezone.utc)
    inactive_bets = []
    for bet in bets_list:
        inactive_flag = True
        end_datetime_str = bet['end_date'] + ' ' + bet['end_time']

        try:
            end_datetime = datetime.strptime(end_datetime_str, '%y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            inactive_flag = end_datetime <= current_utc_date
        except Exception as e:
            logger.warning(f"Date time format is not correct. Will not use for filtering active/inactive: {e}")

        if inactive_flag:
            inactive_bets.append(bet)

    return inactive_bets


@app.route('/get_all_bets', methods=['GET'])
def get_all_bets():
    bets_list, node_info = get_bets_base()

    ret = {
        'bet_list': bets_list,
        'node_info': node_info
    }

    # Reply with json
    return jsonify(ret)


@app.route('/get_active_bets', methods=['GET'])
def get_active_bets():
    bets_list, node_info = get_bets_base()

    active_bets = filter_active_bets(bets_list=bets_list)

    ret = {
        'bet_list': active_bets,
        'node_info': node_info
    }

    # Reply with json
    return jsonify(ret)


@app.route('/get_locked_bets', methods=['GET'])
def get_locked_bets():
    bets_list, node_info = get_bets_base()

    locked_bets = filter_locked_bets(bets_list=bets_list)

    ret = {
        'bet_list': locked_bets,
        'node_info': node_info
    }

    # Reply with json
    return jsonify(ret)


@app.route('/get_inactive_bets', methods=['GET'])
def get_inactive_bets():
    bets_list, node_info = get_bets_base()

    inactive_bets = filter_inactive_bets(bets_list=bets_list)

    ret = {
        'bet_list': inactive_bets,
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

    app.run(host='0.0.0.0', threaded=True, port=APP_PORT, debug=DEBUG_MODE, ssl_context=ssl_context)
