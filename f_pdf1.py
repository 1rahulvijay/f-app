```python
from flask import Flask, render_template, jsonify, send_file, request
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
import io
import json
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

def get_db_connection():
    conn = sqlite3.connect('data/database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
@app.route('/productivity')
@app.route('/fte')
@app.route('/sankey')
def index():
    return render_template('index.html')

@app.route('/api/data')
@app.route('/api/productivity_data')
@app.route('/api/fte_data')
@app.route('/api/sankey_data')
def get_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        path = request.path
        if path == '/api/productivity_data':
            query = '''
                SELECT date, tasks_completed, avg_completion_time, efficiency_rate
                FROM productivity_metrics
                ORDER BY date DESC LIMIT 12
            '''
            cursor.execute(query)
            data = [dict(row) for row in cursor.fetchall()]
            metrics_query = '''
                SELECT tasks_completed, avg_completion_time, efficiency_rate,
                       tasks_completed_trend, tasks_completed_percent_change,
                       avg_completion_time_trend, avg_completion_time_percent_change,
                       efficiency_rate_trend, efficiency_rate_percent_change
                FROM productivity_metrics
                ORDER BY date DESC LIMIT 1
            '''
            cursor.execute(metrics_query)
            metrics = dict(cursor.fetchone())
            data = {
                'lineData': [{'label': row['date'], 'value': row['tasks_completed']} for row in data],
                'barData': [{'label': row['date'], 'value': row['avg_completion_time']} for row in data],
                'areaData': [{'label': row['date'], 'value': row['efficiency_rate']} for row in data],
                'metrics': {'current_metrics': metrics}
            }
        elif path == '/api/fte_data':
            query = '''
                SELECT date, total_fte, utilization, overtime_hours
                FROM fte_metrics
                ORDER BY date DESC LIMIT 12
            '''
            cursor.execute(query)
            data = [dict(row) for row in cursor.fetchall()]
            metrics_query = '''
                SELECT total_fte, utilization, overtime_hours,
                       total_fte_trend, total_fte_percent_change,
                       utilization_trend, utilization_percent_change,
                       overtime_hours_trend, overtime_hours_percent_change
                FROM fte_metrics
                ORDER BY date DESC LIMIT 1
            '''
            cursor.execute(metrics_query)
            metrics = dict(cursor.fetchone())
            data = {
                'lineData': [{'label': row['date'], 'value': row['total_fte']} for row in data],
                'barData': [{'label': row['date'], 'value': row['utilization']} for row in data],
                'areaData': [{'label': row['date'], 'value': row['overtime_hours']} for row in data],
                'metrics': {'current_metrics': metrics}
            }
        elif path == '/api/sankey_data':
            cursor.execute('SELECT * FROM sankey_nodes')
            nodes = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
            cursor.execute('SELECT source, target, value, increase FROM sankey_links')
            links = [dict(row) for row in cursor.fetchall()]
            cursor.execute('SELECT label, value FROM sankey_metrics')
            metrics = [dict(row) for row in cursor.fetchall()]
            data = {'nodes': nodes, 'links': links, 'metrics': metrics}
        else:
            query = '''
                SELECT date, count_id, count_gf, count_gfc, total_tf, ocm_overall
                FROM metrics
                ORDER BY date DESC LIMIT 12
            '''
            cursor.execute(query)
            data = [dict(row) for row in cursor.fetchall()]
            metrics_query = '''
                SELECT count_id, count_gf, count_gfc,
                       count_id_trend, count_id_percent_change,
                       count_gf_trend, count_gf_percent_change,
                       count_gfc_trend, count_gfc_percent_change
                FROM metrics
                ORDER BY date DESC LIMIT 1
            '''
            cursor.execute(metrics_query)
            metrics = dict(cursor.fetchone())
            data = {
                'lineData': [{'label': row['date'], 'value': row['count_id']} for row in data],
                'barData': [{'label': row['date'], 'value': row['count_gf']} for row in data],
                'areaData': [{'label': row['date'], 'value': row['count_gfc']} for row in data],
                'scatterData': [{'label': row['date'], 'total_tf': row['total_tf'], 'ocm_overall': row['ocm_overall']} for row in data],
                'metrics': {'current_metrics': metrics}
            }

        return jsonify(data)
    finally:
        conn.close()

@app.route('/api/annotations', methods=['GET', 'POST'])
def annotations():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if request.method == 'POST':
            data = request.json
            cursor.execute('''
                INSERT INTO annotations (chart_id, page, text, user, reason, exclusion, why, quick_fix, to_do, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['chart_id'], data['page'], data['text'], data['user'],
                data.get('reason'), data.get('exclusion'), data.get('why'),
                data.get('quick_fix'), data.get('to_do'), datetime.now().isoformat()
            ))
            conn.commit()
            return jsonify({'status': 'success'})
        else:
            page = request.args.get('page', '')
            chart_id = request.args.get('chart_id', '')
            query = 'SELECT * FROM annotations WHERE page = ? AND chart_id = ?'
            cursor.execute(query, (page, chart_id))
            annotations = [dict(row) for row in cursor.fetchall()]
            return jsonify(annotations)
    finally:
        conn.close()

@app.route('/api/export_pdf', methods=['POST'])
def export_pdf():
    try:
        pdf_file = request.files['pdf']
        if not pdf_file:
            return jsonify({'error': 'No PDF file provided'}), 400

        # Save the PDF temporarily
        filename = secure_filename(pdf_file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        pdf_file.save(temp_path)

        # Send the file for download
        response = send_file(
            temp_path,
            as_attachment=True,
            download_name='InsightDash_Dashboard.pdf',
            mimetype='application/pdf'
        )

        # Schedule cleanup after response is sent
        @after_this_request
        def cleanup(response):
            try:
                os.remove(temp_path)
                print(f"Deleted temporary file {temp_path}")
            except Exception as e:
                print(f"Failed to delete temporary file {temp_path}: {e}")
            return response

        return response
    except Exception as e:
        print(f"Error in /api/export_pdf: {e}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect', namespace='/annotations')
def handle_connect():
    print('Client connected to annotations namespace')

@socketio.on('disconnect', namespace='/annotations')
def handle_disconnect():
    print('Client disconnected from annotations namespace')

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
```
