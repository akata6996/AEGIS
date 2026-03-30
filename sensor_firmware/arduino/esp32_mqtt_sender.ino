#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "192.168.1.10";

WiFiClient espClient;
PubSubClient client(espClient);

const char* nodeId = "esp32-node-01";
unsigned long seqNum = 0;

void setup_wifi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void reconnect() {
  while (!client.connected()) {
    client.connect(nodeId);
  }
}

void setup() {
  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  char payload[256];
  float sensorValue = 24.0 + (millis() % 100) / 100.0;
  snprintf(
    payload,
    sizeof(payload),
    "{\"node_id\":\"%s\",\"seq_num\":%lu,\"timestamp\":\"2026-01-01T00:00:00Z\",\"sensor_value\":%.2f,\"sensor_type\":\"temperature\",\"unit\":\"C\"}",
    nodeId,
    seqNum,
    sensorValue
  );

  String topic = String("aegis/nodes/") + nodeId + "/telemetry";
  client.publish(topic.c_str(), payload, true);
  seqNum++;
  delay(2000);
}
