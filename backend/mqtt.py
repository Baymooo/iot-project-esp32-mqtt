import json
import pymysql
from datetime import datetime
import paho.mqtt.client as mqtt

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'db': 'iot_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Terhubung ke broker MQTT")
        client.subscribe(topic)
        print(f"📡 Berlangganan ke topic: {topic}")
    else:
        print(f"❌ Gagal konek, kode: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        suhu = data.get('suhu')
        humid = data.get('humidity')
        lux = data.get('lux')

        print(f"Data diterima dari MQTT: suhu={suhu}, humidity={humid}, lux={lux}")

        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO data_sensor (suhu, humidity, lux, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (suhu, humid, lux, datetime.now()))
        conn.commit()
        conn.close()
        print("Data tersimpan ke database.")
    except Exception as e:
        print("Error saat proses pesan:", e)

broker = "broker.hivemq.com"
topic = "iot/bimo/sensor"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_log = lambda c, u, l, s: print("Log:", s)

client.connect(broker, 1883, 60)
print("Subscriber berjalan, menunggu data dari ESP32...")
client.loop_forever()
