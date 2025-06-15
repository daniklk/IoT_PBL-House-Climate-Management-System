from flask import Flask, request, jsonify, render_template, abort
import sqlite3
import requests
from make_hex import generate_ir_signal  # должен быть свой файл

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


@app.route('/api/send-ir', methods=['POST'])
def send_ir_command():
    try:
        data = request.get_json()
        required = ['protocol', 'device', 'subdevice', 'function']
        for key in required:
            if key not in data:
                return jsonify({'error': f'Missing {key}'}), 400

        protocol = data['protocol']
        device = data['device']
        subdevice = data['subdevice']
        function = data['function']

        ir_result = generate_ir_signal(protocol, device, subdevice, function)

        if ir_result['success']:
            log_ir_command(protocol, device, subdevice, function, ir_result['output'], 'success')
            return jsonify({
                'status': 'success',
                'ir_output': ir_result['output'],
                'command': {
                    'protocol': protocol,
                    'device': device,
                    'subdevice': subdevice,
                    'function': function
                }
            }), 200
        else:
            log_ir_command(protocol, device, subdevice, function, ir_result['error'], 'failed')
            return jsonify({'status': 'error', 'details': ir_result['error']}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'details': str(e)}), 500


def log_ir_command(protocol, device, subdevice, function, ir_output, status):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ir_commands (protocol, device, subdevice, function, ir_output, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (protocol, device, subdevice, function, ir_output, status))
    conn.commit()
    conn.close()


@app.route('/device/<company>/<path:device_path>')
def device_page(company, device_path):
    url = f'https://cdn.jsdelivr.net/gh/probonopd/irdb@master/codes/{company}/{device_path}'
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception:
        return "Failed to fetch device data", 500

    lines = resp.text.strip().split('\n')
    buttons = []
    for line in lines[1:]:
        parts = line.split(',')
        if parts:
            buttons.append(parts[0])

    return render_template(
        'device.html',
        company=company,
        device=device_path,
        buttons=buttons,
        protocol='NEC',       # можно заменить
        device_id='1',
        subdevice_id='1'
    )


@app.route('/company/<company_name>')
def company_page(company_name):
    grouped = fetch_and_group_data()
    if grouped is None:
        return "Failed to fetch data", 500

    devices = grouped.get(company_name)
    if devices is None:
        abort(404)

    return render_template('company.html', company=company_name, devices=devices)


@app.route('/companies')
def companies_list():
    grouped = fetch_and_group_data()
    if grouped is None:
        return "Failed to fetch data", 500

    companies = sorted(grouped.keys())
    return render_template('companies.html', companies=companies)


@app.route('/')
def index():
    return render_template('index.html')


def fetch_and_group_data():
    url = 'https://cdn.jsdelivr.net/gh/probonopd/irdb@master/codes/index'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception:
        return None

    lines = response.text.strip().split('\n')
    grouped = {}
    for line in lines:
        parts = line.split('/')
        if len(parts) < 1:
            continue
        company = parts[0]
        rest = '/'.join(parts[1:]) if len(parts) > 1 else ''
        if company not in grouped:
            grouped[company] = []
        grouped[company].append(rest)
    return grouped


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
