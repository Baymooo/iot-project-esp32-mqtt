#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"
#include <Wire.h>
#include "RTClib.h"

// --- Konfigurasi WiFi ---
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// --- Konfigurasi MQTT ---
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* topic_publish = "iot/bimo/sensor";
const char* topic_subscribe = "iot/bimo/relay";

WiFiClient espClient;
PubSubClient client(espClient);

// --- Sensor DHT ---
#define DHTPIN 3
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// --- Sensor Cahaya (LDR Module) ---
#define LDR_PIN 34

// --- Relay ---
#define RELAY_PIN 25   // pin kontrol relay ke GPIO25

// --- RTC DS1307 ---
RTC_DS1307 rtc;

// --- Fungsi koneksi WiFi ---
void setup_wifi() {
  delay(10);
  Serial.println("Menghubungkan ke WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Terhubung!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// --- Callback pesan dari MQTT ---
void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Pesan diterima dari topic: ");
  Serial.println(topic);

  String pesan = "";
  for (int i = 0; i < length; i++) {
    pesan += (char)message[i];
  }
  Serial.print("Isi pesan: ");
  Serial.println(pesan);

  // --- Kontrol Relay ---
  if (pesan == "ON") {
    digitalWrite(RELAY_PIN, HIGH);  // aktifkan relay
    Serial.println("Relay AKTIF");
  } else if (pesan == "OFF") {
    digitalWrite(RELAY_PIN, LOW);   // matikan relay
    Serial.println("Relay NONAKTIF");
  }
}

// --- Reconnect ke MQTT broker ---
void reconnect() {
  while (!client.connected()) {
    Serial.print("Menghubungkan ke MQTT...");
    String clientId = "ESP32Client-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("Terhubung!");
      client.subscribe(topic_subscribe);
    } else {
      Serial.print("Gagal, rc=");
      Serial.print(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  dht.begin();

  // NTP untuk waktu real
  configTime(7 * 3600, 0, "pool.ntp.org"); // UTC+7 Indonesia
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  float suhu = dht.readTemperature();
  float lembap = dht.readHumidity();
  int lux = analogRead(LDR_PIN);

  if (isnan(suhu) || isnan(lembap)) {
    Serial.println("Gagal membaca data DHT22!");
    return;
  }

  // Ambil waktu NTP
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("Gagal mendapatkan waktu NTP");
    return;
  }

  char waktu[30];
  strftime(waktu, sizeof(waktu), "%Y-%m-%d %H:%M:%S", &timeinfo);

  String jsonData = "{";
  jsonData += "\"id\": 1, ";
  jsonData += "\"suhu\": " + String(suhu, 2) + ", ";
  jsonData += "\"humidity\": " + String(lembap, 2) + ", ";
  jsonData += "\"lux\": " + String(lux) + ", ";
  jsonData += "\"timestamp\": \"" + String(waktu) + "\"";
  jsonData += "}";

  boolean status = client.publish(topic_publish, jsonData.c_str());
  if (status)
    Serial.println("Publish berhasil!");
  else
    Serial.println("Publish gagal!");

  Serial.println(jsonData);
  delay(5000);
}