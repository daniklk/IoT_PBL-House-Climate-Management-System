from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
from make_hex import generate_ir_signal

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL,
            humidity REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ir_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocol TEXT,
            device TEXT,
            subdevice TEXT,
            function TEXT,
            ir_output TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    temperature = data.get('temperature')
    humidity = data.get('humidity')

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO readings (temperature, humidity) VALUES (?, ?)', (temperature, humidity))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'}), 201


@app.route('/api/readings', methods=['GET'])
def get_readings():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT temperature, humidity, timestamp FROM readings ORDER BY timestamp DESC LIMIT 20')
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)


@app.route('/api/send-ir', methods=['POST'])
def send_ir_command():
    try:
        data = request.get_json()

        required_fields = ['protocol', 'device', 'subdevice', 'function']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        protocol = str(data['protocol'])
        device = str(data['device'])
        subdevice = str(data['subdevice'])
        function = str(data['function'])

        ir_result = generate_ir_signal(protocol, device, subdevice, function)

        if ir_result['success']:
            log_ir_command(protocol, device, subdevice, function, ir_result['output'], "success")

            return jsonify({
                'status': 'success',
                'message': 'IR command sent successfully',
                'ir_output': ir_result['output'],
                'command_sent': {
                    'protocol': protocol,
                    'device': device,
                    'subdevice': subdevice,
                    'function': function
                }
            }), 200
        else:
            log_ir_command(protocol, device, subdevice, function, ir_result['error'], "failed")
            return jsonify({
                'status': 'error',
                'error': 'Failed to generate IR signal',
                'details': ir_result['error']
            }), 500

    except Exception as e:
        log_ir_command('unknown', 'unknown', 'unknown', 'unknown', str(e), "error")
        return jsonify({'error': str(e)}), 500


def log_ir_command(protocol, device, subdevice, function, ir_output, status):
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO ir_commands (protocol, device, subdevice, function, ir_output, status) VALUES (?, ?, ?, ?, ?, ?)',
            (protocol, device, subdevice, function, ir_output, status)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log IR command: {e}")


@app.route('/api/ir-history', methods=['GET'])
def get_ir_commands():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT protocol, device, subdevice, function, ir_output, status, timestamp FROM ir_commands ORDER BY timestamp DESC LIMIT 50')
    rows = cursor.fetchall()
    conn.close()

    commands = []
    for row in rows:
        commands.append({
            'protocol': row[0],
            'device': row[1],
            'subdevice': row[2],
            'function': row[3],
            'ir_output': row[4],
            'status': row[5],
            'timestamp': row[6]
        })

    return jsonify(commands)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
