from flask import Flask, jsonify, request
import pymysql
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Konfigurasi Database
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'db': 'iot_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)

@app.route('/api/sensor', methods=['GET'])
def sensor_json():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(suhu) AS suhu_max, MIN(suhu) AS suhu_min, AVG(suhu) AS suhu_avg FROM data_sensor")
            r = cur.fetchone()
            suhumax = int(r['suhu_max']) if r['suhu_max'] is not None else None
            suhumin = int(r['suhu_min']) if r['suhu_min'] is not None else None
            suhurata = round(r['suhu_avg'], 2) if r['suhu_avg'] is not None else None
            cur.execute("""
                SELECT id AS idx, suhu, humidity AS humid, lux AS kecerahan, timestamp
                FROM data_sensor
                ORDER BY suhu DESC, humidity DESC
            """)
            rows = cur.fetchall()
            nilai_suhu_max_humid_max = []
            for row in rows:
                nilai_suhu_max_humid_max.append({
                    "idx": row['idx'],
                    "suhun": int(row['suhu']) if row['suhu'] is not None else None,
                    "humid": int(row['humid']) if row['humid'] is not None else None,
                    "kecerahan": int(row['kecerahan']) if row['kecerahan'] is not None else None,
                    "timestamp": row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                })
            cur.execute("""
                SELECT MONTH(timestamp) AS month, YEAR(timestamp) AS year, MAX(suhu) AS max_suhu
                FROM data_sensor
                GROUP BY YEAR(timestamp), MONTH(timestamp)
                ORDER BY max_suhu DESC
            """)
            my = cur.fetchall()
            month_year_max = []
            for rmy in my:
                month_year_max.append({
                    "month_year": f"{rmy['month']}-{rmy['year']}"
                })

            result = {
                "suhumax": suhumax,
                "suhumin": suhumin,
                "suhurata": suhurata,
                "nilai_suhu_max_humid_max": nilai_suhu_max_humid_max,
                "month_year_max": month_year_max
            }

            return jsonify(result), 200
    finally:
        conn.close()

@app.route('/api/sensor', methods=['POST'])
def insert_sensor():
    conn = get_conn()
    try:
        data = request.get_json()
        suhu = data.get('suhu')
        humid = data.get('humidity')
        lux = data.get('lux')

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO data_sensor (suhu, humidity, lux, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (suhu, humid, lux, datetime.now()))
        conn.commit()

        return jsonify({"message": "Data berhasil disimpan!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
