#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <IRremote.h>

const char* ssid = "Pixel_4133";
const char* password = "maniak777";
const char* serverUrl = "http://192.168.0.220:5000/api/data";

#define DHTPIN 26
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// IR LED connected to GPIO 25
#define IR_SEND_PIN 25

unsigned long previousMillis = 0;
const long readInterval = 6000;
unsigned long lastIRMillis = 0;
const long irInterval = 5000;

float lastTemp = 0;
float lastHum = 0;

void readAndSendSensorData();
void sendIRCommand();

void setup() {
  Serial.begin(115200);
  dht.begin();
  delay(2000);  // DHT stabilization

  Serial.println("Testing DHT sensor...");
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) {
    Serial.println("Initial DHT read failed!");
  } else {
    Serial.printf("Initial Temp: %.2f °C, Hum: %.2f %%\n", t, h);
  }

  // Start IR
  IrSender.begin(IR_SEND_PIN);

  // Connect WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP address: " + WiFi.localIP().toString());
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= readInterval) {
    previousMillis = currentMillis;
    readAndSendSensorData();
  }

  if (lastTemp > 5.0 && currentMillis - lastIRMillis >= irInterval) {
    lastIRMillis = currentMillis;
    sendIRCommand();
  }
}

void readAndSendSensorData() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  lastTemp = temperature;
  lastHum = humidity;

  Serial.printf("Temp: %.2f °C, Hum: %.2f %%\n", temperature, humidity);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"temperature\": " + String(temperature, 2) + ", \"humidity\": " + String(humidity, 2) + "}";
    int responseCode = http.POST(payload);

    Serial.print("POST response code: ");
    Serial.println(responseCode);
    http.end();
  } else {
    Serial.println("WiFi not connected. Skipping POST.");
  }
}

void sendIRCommand() {
  Serial.println("Sending IR signal...");
  IrSender.sendNECMSB(0x20DF10EF, 32);  // Example code
}