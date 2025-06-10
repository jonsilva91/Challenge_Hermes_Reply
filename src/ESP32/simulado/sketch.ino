#include <Arduino.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <ArduinoJson.h>
#include <LiquidCrystal_I2C.h>

// ——— LCD I2C 20×4 no endereço 0x27 ———
LiquidCrystal_I2C LCD(0x27, 20, 4);

// ——— Pinos analógicos ———
const int PIN_VIB = 34;
const int PIN_CUR = 35;
const int PIN_MIP = 32;

// ——— DS18B20 (one–wire) ———
const int ONE_WIRE_PIN = 4;
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature ds18b20(&oneWire);

// ——— MPU6050 (I²C) ———
Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);

  // inicia LCD (Wire.begin nos pinos padrão SDA=21/SCL=22)
  Wire.begin();
  LCD.init();
  LCD.backlight();
  LCD.clear();
  LCD.setCursor(0,0);
  LCD.print("Inicializando...");

  // DS18B20
  pinMode(ONE_WIRE_PIN, INPUT_PULLUP);
  ds18b20.begin();

  // MPU6050
  if (!mpu.begin()) {
    LCD.setCursor(0,1);
    LCD.print("MPU6050 nao iniciado");
    while (1);
  }

  delay(500);
  LCD.clear();
}

void loop() {
  // —— leituras analógicas ——
  float vib_g = analogRead(PIN_VIB) / 4095.0 * 3.3;
  float frac  = analogRead(PIN_CUR) / 4095.0;
  float cur_A = frac * 10.0;             // simula 0–10 A
  float press = analogRead(PIN_MIP) / 4095.0 * 100.0;

  // —— leitura DS18B20 ——
  ds18b20.requestTemperatures();
  float tempC = ds18b20.getTempCByIndex(0);

  // —— leitura MPU6050 ——
  sensors_event_t accEvt, gyrEvt, tmpEvt;
  mpu.getEvent(&accEvt, &gyrEvt, &tmpEvt);
  float accelX = accEvt.acceleration.x;

  // —— monta JSON e imprime no Serial ——
  StaticJsonDocument<256> doc;
  doc["vibration_g"]  = vib_g;
  doc["current_A"]    = cur_A;
  doc["pressure_psi"] = press;
  doc["temp_C"]       = tempC;
  doc["accel_x"]      = accelX;

  String json;
  serializeJson(doc, json);
  Serial.println(json);

  // —— exibe no LCD ——
  LCD.clear();
  LCD.setCursor(0,0);
  LCD.printf("V:%.2fg C:%.1fA", vib_g, cur_A);
  LCD.setCursor(0,1);
  LCD.printf("P:%.0fpsi T:%.1fC", press, tempC);
  LCD.setCursor(0,2);
  LCD.printf("A:%.2fm/s2", accelX);

  delay(1000);
}
