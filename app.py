import os
import logging
import sqlite3

from flask_cors import CORS
from datetime import datetime, timezone
from flask import Flask, request, jsonify

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
PAGINATION_THRESHOLD = 100

PAGINATIONS_FILTER = [
    "bet_id",
    "open_date",
    "open_time",
    "close_date",
    "close_time",
    "end_date",
    "end_time",
    "creator",
    "max_slot_per_option",
    "amount_per_bet_slot",
    "no_ops",
    "no_options",
    "option_desc",
    "result",
    "status",
    "oracle_id",
    "bet_desc",
    "oracle_vote"
]

# This filter apply for containing check
CONTAINING_FILTER = [
    "open_date",
    "open_time",
    "close_date",
    "close_time",
    "end_date",
    "end_time",
    "creator",
    "option_desc",
    "oracle_id",
    "bet_desc",
    "oracle_vote"
]


def pagination_filter(bets_list):
    
    filtered_bets = bets_list
    for pagin in PAGINATIONS_FILTER:
        pagin_filter = request.args.get(pagin)
        if pagin_filter:
            # This only checks for containing
            if pagin in CONTAINING_FILTER:
                filtered_bets = list(filter(lambda p: pagin_filter in p[pagin], filtered_bets))
            else:  # Check for match all
                filtered_bets = list(filter(lambda p: str(p[pagin]) == pagin_filter, filtered_bets))

    return filtered_bets

def pagination_page(bets_list, page, page_size):
    
    filtered_bets = bets_list

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_bets = filtered_bets[start:end]

    return paginated_bets

# Get the data with pargination for the http request
def apply_pagination(bets_list):
   
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', PAGINATION_THRESHOLD))

    # Filter
    filtered_bets = pagination_filter(bets_list)

    # Get the result with pagination
    if len(filtered_bets) > page_size:
        total_records = len(filtered_bets)
        paginated_bets = pagination_page(filtered_bets, page, page_size)
        ret = {
            'bet_list': paginated_bets,
            'page': {
                "current_records" : len(paginated_bets),
                "total_records": total_records,
                "current_page": page,
                "page_size": page_size,
                "total_pages": (total_records + page_size - 1) // page_size  # Calculate total pages
            }
        }
    else:
        ret = {
            'bet_list': filtered_bets,
            'page': {
                "current_records" : len(filtered_bets),
                "total_records": len(filtered_bets),
                "current_page": 1,
                "page_size": len(filtered_bets),
                "total_pages": 1
            }
        }
    return ret

def get_bets_base():
    if not os.path.isfile(DATABASE_FILE):
        logger.warning(f"No database found at {DATABASE_FILE}. Please wait...")
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
    filtered_bets = list(filter(lambda p: p['result'] < 0, bets_list))

    # Check the closed date and close time
    current_utc_date = datetime.now(timezone.utc)
    active_bets = []
    for bet in filtered_bets:
        active_flag = False
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
        locked_flag = False
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
    # Inactive bet is a bet that has result
    inactive_bets_results = list(filter(lambda p: p['result'] >= 0, bets_list))

    # Check the end date and close time
    current_utc_date = datetime.now(timezone.utc)
    inactive_bets_datetime = []
    for bet in bets_list:
        inactive_flag = False
        end_datetime_str = bet['end_date'] + ' ' + bet['end_time']

        try:
            end_datetime = datetime.strptime(end_datetime_str, '%y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            inactive_flag = end_datetime <= current_utc_date
        except Exception as e:
            logger.warning(f"Date time format is not correct. Will not use for filtering active/inactive: {e}")

        if inactive_flag:
            inactive_bets_datetime.append(bet)

    return inactive_bets_datetime + inactive_bets_results


@app.route('/get_all_bets', methods=['GET'])
def get_all_bets():
    bets_list, node_info = get_bets_base()

    # Apply pagination
    ret = apply_pagination(bets_list)

    # Add the node info
    ret['node_info'] = node_info

    # Reply with json
    return jsonify(ret)


@app.route('/get_active_bets', methods=['GET'])
def get_active_bets():
    bets_list, node_info = get_bets_base()

    active_bets = filter_active_bets(bets_list=bets_list)

    # Apply pagination
    ret = apply_pagination(active_bets)

    # Add the node info
    ret['node_info'] = node_info

    # Reply with json
    return jsonify(ret)


@app.route('/get_locked_bets', methods=['GET'])
def get_locked_bets():
    bets_list, node_info = get_bets_base()

    locked_bets = filter_locked_bets(bets_list=bets_list)

    # Apply pagination
    ret = apply_pagination(locked_bets)

    # Add the node info
    ret['node_info'] = node_info

    # Reply with json
    return jsonify(ret)


@app.route('/get_inactive_bets', methods=['GET'])
def get_inactive_bets():
    bets_list, node_info = get_bets_base()

    inactive_bets = filter_inactive_bets(bets_list=bets_list)

    # Apply pagination
    ret = apply_pagination(inactive_bets)

    # Add the node info
    ret['node_info'] = node_info

    # Reply with json
    return jsonify(ret)

@app.route('/get_available_filters', methods=['GET'])
def get_filter():

    # Add the node info
    ret = {'available_filters': PAGINATIONS_FILTER}

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

    PAGINATION_THRESHOLD = int(os.getenv('PAGINATION_THRESHOLD',
                                         PAGINATION_THRESHOLD))  # Default threshold for pagination

    # Print the configuration to verify
    logger.info("Launch the flask app with configurations")
    logger.info(f"- App port: {APP_PORT}")
    logger.info(f"- Database read location: {DATABASE_FILE}")
    logger.info(f"- Debug mode: {DEBUG_MODE}")
    logger.info(f"- Pagination threshold: {PAGINATION_THRESHOLD}")

    # Insert the ssl crt and key here
    ssl_context = (os.getenv('CERT_PATH'), os.getenv('CERT_KEY_PATH'))
    if DEBUG_MODE:
        ssl_context = 'adhoc'

    app.run(host='0.0.0.0', threaded=True, port=APP_PORT, debug=DEBUG_MODE, ssl_context=ssl_context)
