from flask import Flask, request, jsonify, render_template, abort
import sqlite3
from datetime import datetime
import requests

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

@app.route('/company/<company_name>')
def company_page(company_name):
    grouped = fetch_and_group_data()
    if grouped is None:
        return "Failed to fetch data", 500

    devices = grouped.get(company_name)
    if devices is None:
        abort(404, description="Company not found")

    return render_template('company.html', company=company_name, devices=devices)

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
    for line in lines[1:]:  # пропускаем заголовок
        parts = line.split(',')
        if parts:
            buttons.append(parts[0])  # functionname

    return render_template('device.html', company=company, device=device_path, buttons=buttons)

@app.route('/companies')
def companies_list():
    grouped = fetch_and_group_data()
    if grouped is None:
        return "Failed to fetch data", 500

    companies = sorted(grouped.keys())
    q = request.args.get('q', '').lower()
    if q:
        companies = [c for c in companies if q in c.lower()]

    return render_template('companies.html', companies=companies)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
