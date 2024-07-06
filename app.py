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
    "oracle_id",
    "bet_desc"
]


def filter_pagination(bets_list, page, page_size):
    filtered_bets = bets_list
    for pagin in PAGINATIONS_FILTER:
        pagin_filter = request.args.get(pagin)
        if pagin_filter:
            # This only checks for containing
            if pagin == 'bet_desc' or pagin == 'oracle_id':
                filtered_bets = list(filter(lambda p: pagin_filter in p[pagin], filtered_bets))
            else:  # Check for match all
                filtered_bets = list(filter(lambda p: p[pagin] == pagin_filter, filtered_bets))

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_bets = filtered_bets[start:end]

    return paginated_bets, len(filtered_bets)


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
    filtered_bets = list(filter(lambda p: p['result'] >= 0, bets_list))

    # Check the end date and close time
    current_utc_date = datetime.now(timezone.utc)
    inactive_bets = []
    for bet in filtered_bets:
        inactive_flag = False
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

    # Get pagination parameters
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', PAGINATION_THRESHOLD))

    if len(bets_list) > PAGINATION_THRESHOLD:
        print('a')
        filtered_bets, total_records = filter_pagination(bets_list, page, page_size)
        ret = {
            'bet_list': filtered_bets,
            'node_info': node_info,
            'paginations': PAGINATIONS_FILTER,
            'page': {
                "total_records": len(bets_list),
                "current_page": page,
                "page_size": page_size,
                "total_pages": (total_records + page_size - 1) // page_size  # Calculate total pages
            }
        }
    else:
        print('b')
        ret = {
            'bet_list': bets_list,
            'node_info': node_info,
            'paginations': PAGINATIONS_FILTER,
            'page': {
                "total_records": len(bets_list),
                "current_page": 1,
                "page_size": len(bets_list),
                "total_pages": 1
            }
        }

    # Reply with json
    return jsonify(ret)


@app.route('/get_active_bets', methods=['GET'])
def get_active_bets():
    bets_list, node_info = get_bets_base()

    # Get pagination parameters
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', PAGINATION_THRESHOLD))

    active_bets = filter_active_bets(bets_list=bets_list)

    if len(active_bets) > PAGINATION_THRESHOLD:
        paginated_bets, total_records = filter_pagination(active_bets, page, page_size)
        ret = {
            'bet_list': paginated_bets,
            'node_info': node_info,
            'page': {
                "total_records": total_records,
                "current_page": page,
                "page_size": page_size,
                "total_pages": (total_records + page_size - 1) // page_size  # Calculate total pages
            }
        }
    else:
        ret = {
            'bet_list': active_bets,
            'node_info': node_info,
            'page': {
                "total_records": len(active_bets),
                "current_page": 1,
                "page_size": len(active_bets),
                "total_pages": 1
            }
        }

    # Reply with json
    return jsonify(ret)


@app.route('/get_locked_bets', methods=['GET'])
def get_locked_bets():
    bets_list, node_info = get_bets_base()

    # Get pagination parameters
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', PAGINATION_THRESHOLD))

    locked_bets = filter_locked_bets(bets_list=bets_list)

    if len(locked_bets) > PAGINATION_THRESHOLD:
        paginated_bets, total_records = filter_pagination(locked_bets, page, page_size)
        ret = {
            'bet_list': paginated_bets,
            'node_info': node_info,
            'page': {
                "total_records": total_records,
                "current_page": page,
                "page_size": page_size,
                "total_pages": (total_records + page_size - 1) // page_size  # Calculate total pages
            }
        }
    else:
        ret = {
            'bet_list': locked_bets,
            'node_info': node_info,
            'page': {
                "total_records": len(locked_bets),
                "current_page": 1,
                "page_size": len(locked_bets),
                "total_pages": 1
            }
        }

    # Reply with json
    return jsonify(ret)


@app.route('/get_inactive_bets', methods=['GET'])
def get_inactive_bets():
    bets_list, node_info = get_bets_base()

    # Get pagination parameters
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', PAGINATION_THRESHOLD))

    inactive_bets = filter_inactive_bets(bets_list=bets_list)

    if len(inactive_bets) > PAGINATION_THRESHOLD:
        paginated_bets, total_records = filter_pagination(inactive_bets, page, page_size)
        ret = {
            'bet_list': paginated_bets,
            'node_info': node_info,
            'page': {
                "total_records": total_records,
                "current_page": page,
                "page_size": page_size,
                "total_pages": (total_records + page_size - 1) // page_size  # Calculate total pages
            }
        }
    else:
        ret = {
            'bet_list': inactive_bets,
            'node_info': node_info,
            'page': {
                "total_records": len(inactive_bets),
                "current_page": 1,
                "page_size": len(inactive_bets),
                "total_pages": 1
            }
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
