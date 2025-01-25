from flask import Blueprint, jsonify, request
from datetime import datetime
from app.services import cache
import json

bp = Blueprint('api', __name__)
MAX_HISTORY_LENGTH = 1000


def transform_data(data):
    """Transform raw device data into standardized format with calculations."""
    current_time = datetime.now().isoformat()

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    voltage = float(data.get('voltage', 0))
    current = float(data.get('current', 0))
    angle = float(data.get('angle', 0))

    return {
        'timestamp': current_time,
        'voltage': voltage,
        'current': current,
        'angle': angle,
        'power': voltage * current
    }


def store_data(data):
    """Store data in cache with size limit handling."""
    historical = cache.get('historical') or []
    historical.append(data)
    if len(historical) > MAX_HISTORY_LENGTH:
        historical = historical[-MAX_HISTORY_LENGTH:]
    cache.set('historical', historical)
    cache.set('current_state', data)


def store_fault(fault_data):
    """Store fault notification in cache."""
    current_time = datetime.now().isoformat()
    fault_record = {
        'timestamp': current_time,
        'fault': fault_data.get('fault'),
        'message': fault_data.get('message'),
        'resolved': False
    }

    fault_history = cache.get('fault_history') or []
    fault_history.append(fault_record)

    if len(fault_history) > 100:
        fault_history = fault_history[-100:]

    cache.set('fault_history', fault_history)
    cache.set('current_fault', fault_record)


def clear_current_fault():
    """Clear the current fault and update history."""
    current_fault = cache.get('current_fault')
    if current_fault:
        current_fault['resolved'] = True
        current_fault['resolved_time'] = datetime.now().isoformat()

        # Update the fault in history
        fault_history = cache.get('fault_history') or []
        if fault_history:
            for fault in reversed(fault_history):
                if fault['timestamp'] == current_fault['timestamp']:
                    fault.update(current_fault)
                    break

        cache.set('fault_history', fault_history)
        cache.set('current_fault', None)
        return True
    return False


@bp.route('/data/current', methods=['GET'])
def get_current_data():
    """Get most recent device state."""
    current_state = cache.get('current_state')
    if not current_state:
        return jsonify({'error': 'No data available'}), 404
    return jsonify(current_state)


@bp.route('/data/historical', methods=['GET'])
def get_historical_data():
    """Get historical device data."""
    historical = cache.get('historical')
    if not historical:
        return jsonify({'error': 'No historical data available'}), 404
    return jsonify(historical)


@bp.route('/fault/current', methods=['GET'])
def get_current_fault():
    """Get current fault status."""
    current_fault = cache.get('current_fault')
    if not current_fault:
        return jsonify({'fault': False, 'message': 'No active fault'}), 200
    return jsonify(current_fault)


@bp.route('/fault/clear', methods=['POST'])
def clear_fault():
    """Clear the current fault."""
    if clear_current_fault():
        return jsonify({
            'message': 'Fault cleared successfully',
            'status': 'cleared'
        }), 200
    return jsonify({
        'message': 'No active fault to clear',
        'status': 'no_fault'
    }), 200


@bp.route('/fault/history', methods=['GET'])
def get_fault_history():
    """Get fault history."""
    fault_history = cache.get('fault_history')
    if not fault_history:
        return jsonify({'error': 'No fault history available'}), 404
    return jsonify(fault_history)


@bp.route('/fault', methods=['POST'])
def handle_fault():
    """Handle incoming fault notifications."""
    try:
        fault_data = request.get_json()
        if not fault_data:
            return jsonify({'error': 'No fault data provided'}), 400

        store_fault(fault_data)

        return jsonify({
            'message': 'Fault notification received',
            'status': 'recorded'
        }), 200

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'message': 'success'}), 200


@bp.route('/data', methods=['POST'])
def handle_device_data():
    """Handle incoming device data via HTTP POST."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        transformed_data = transform_data(data)
        store_data(transformed_data)

        return jsonify({
            'message': 'Data received successfully',
            'data': transformed_data
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
