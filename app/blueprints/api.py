from flask import Blueprint, jsonify
from datetime import datetime
from app.services import cache
from flask_socketio import emit
from flask_socketio import SocketIO

bp = Blueprint('api', __name__)
socketio = SocketIO()

MAX_HISTORY_LENGTH = 1000


def transform_data(data):
    current_time = datetime.now().isoformat()
    return {
        'timestamp': current_time,
        'voltage': data.get('V'),
        'current': data.get('C'),
        'angle': data.get('A'),
        'power': data.get('V', 0) * data.get('C', 0)
    }


def store_data(data):
    historical = cache.get('historical') or []
    historical.append(data)
    if len(historical) > MAX_HISTORY_LENGTH:
        historical = historical[-MAX_HISTORY_LENGTH:]
    cache.set('historical', historical)
    cache.set('current_state', data)


@bp.route('/data/current', methods=['GET'])
def get_current_data():
    current_state = cache.get('current_state')
    if not current_state:
        return jsonify({'error': 'No data available'}), 404
    return jsonify(current_state)


@bp.route('/data/historical', methods=['GET'])
def get_historical_data():
    historical = cache.get('historical')
    if not historical:
        return jsonify({'error': 'No historical data available'}), 404
    return jsonify(historical)


@bp.route('/health', methods=['GET'])
def health():
    return jsonify({'message': 'success'}), 200


@socketio.on('device_data')
def handle_device_data(data):
    try:
        transformed_data = transform_data(data)
        store_data(transformed_data)
        emit('data_update', transformed_data, broadcast=True)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
