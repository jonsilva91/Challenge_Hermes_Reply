#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_TMP117.h>
#include <Adafruit_MAX31865.h>
#include <Adafruit_INA219.h>
// #include <Adafruit_IIS3DWB.h>  // quando implementar
// #include <PDM.h>               // SPH0641LU4H-1
// #include <driver/i2s.h>        // ICS-43434

// ---- Definições de pino (padrão ou via build_flags) ----
#ifndef ADC_VIB_PIN
  #define ADC_VIB_PIN      34    // ADXL1002 (analógico)
#endif
#ifndef ADC_ACS770_PIN
  #define ADC_ACS770_PIN   35    // ACS770 (analógico)
#endif
#ifndef ADC_MIP_PIN
  #define ADC_MIP_PIN      32    // Honeywell MIP (analógico)
#endif
#ifndef PIN_CS_MAX31865
  #define PIN_CS_MAX31865  5     // PT100 via MAX31865 (SPI CS)
#endif
#ifndef PIN_CS_IIS3DWB
  #define PIN_CS_IIS3DWB   17    // IIS3DWB (SPI CS)
#endif

// ---- Instâncias dos sensores I2C/SPI ----
Adafruit_TMP117   tmp117   = Adafruit_TMP117();
Adafruit_MAX31865 max31865 = Adafruit_MAX31865(PIN_CS_MAX31865);
Adafruit_INA219   ina219   = Adafruit_INA219();
// Adafruit_IIS3DWB  iis3dwb  = Adafruit_IIS3DWB(&Wire); // quando implementar

// ---- Credenciais Wi-Fi & MQTT ----
const char* SSID        = "SEU_SSID";
const char* PASS        = "SUA_SENHA";
const char* MQTT_BROKER = "broker.exemplo.com";
const uint16_t MQTT_PORT = 1883;
const char* MQTT_USER   = "user";
const char* MQTT_PASS   = "pass";

// ---- Objetos de rede ----
WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);

void connectWiFi() {
  Serial.print("Conectando ao WiFi…");
  WiFi.begin(SSID, PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.println(" conectado!");
}

void connectMQTT() {
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  Serial.print("Conectando ao MQTT…");
  while (!mqtt.connected()) {
    if (mqtt.connect("ESP32Client", MQTT_USER, MQTT_PASS)) {
      Serial.println(" OK!");
    } else {
      Serial.print(" falhou, rc=");
      Serial.print(mqtt.state());
      Serial.println(" — tentando em 2s");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(100);

  connectWiFi();
  connectMQTT();

  Wire.begin();
  SPI.begin();

  // Inicializa TMP117
  if (!tmp117.begin()) {
    Serial.println("Erro ao inicializar TMP117");
    while (1);
  }

  // Inicializa INA219
  ina219.begin();

  // Inicializa MAX31865 (PT100)
  max31865.begin(MAX31865_3WIRE);

  Serial.println("Sensores iniciados!");
}

void loop() {
  // Reconnect se necessário
  if (!mqtt.connected()) {
    connectMQTT();
  }
  mqtt.loop();

  // --- Leituras Analógicas ---
  int raw_vib = analogRead(ADC_VIB_PIN);
  float vib_g = (raw_vib / 4095.0) * 3.3;  // ajuste de escala conforme o circuito

  int raw_cur = analogRead(ADC_ACS770_PIN);
  float cur_A = ((raw_cur / 4095.0) * 3.3 - 2.5) / 0.040;  // ex: 40mV/A sensibilidade

  int raw_mip = analogRead(ADC_MIP_PIN);
  float press_mip = (raw_mip / 4095.0) * 100.0;  // exemplo: 0–100 psi

  // --- Leitura TMP117 (I2C) ---
  sensors_event_t evt;
  tmp117.getEvent(&evt);
  float temp_i2c = evt.temperature;

  // --- Leitura PT100 via MAX31865 ---
  float temp_pt100 = max31865.temperature(100.0, 430.0);

  // --- Leitura INA219 (I2C) ---
  float bus_v   = ina219.getBusVoltage_V();
  float shunt_v = ina219.getShuntVoltage_mV() / 1000.0;
  float curr_mA = ina219.getCurrent_mA();

  // --- Placeholder para IIS3DWB ---
  float accel_digital = 0.0;  // TODO: implementar iis3dwb.getEvent(&evtAcc)

  // --- Monta JSON ---
  StaticJsonDocument<256> doc;
  doc["vibration_g"]   = vib_g;
  doc["accel_digital"] = accel_digital;
  doc["temp_i2c"]      = temp_i2c;
  doc["temp_pt100"]    = temp_pt100;
  doc["current_A"]     = cur_A;
  doc["bus_V"]         = bus_v;
  doc["shunt_V"]       = shunt_v;
  doc["current_mA"]    = curr_mA;
  doc["pressure_mip"]  = press_mip;

  char payload[256];
  size_t len = serializeJson(doc, payload);

  // Publica via MQTT
  mqtt.publish("industrial/sensors", payload, len);

  // Debug no Serial
  Serial.println(payload);

  delay(1000);
}
