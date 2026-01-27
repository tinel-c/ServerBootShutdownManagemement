/*
 * SMS Gateway for ESP32 with SIM800
 * Integrated with ServerBootShutdownManagement project
 * 
 * This device connects to MQTT broker and provides SMS send/receive capabilities
 * through the automation platform.
 * 
 * Hardware: LilyGo T-Call SIM800
 * MQTT Topics: sms/gateway/*
 * 
 * Features:
 * - Self-recovery and error handling
 * - Reset detection and announcement
 * - WiFi failure SMS notifications
 * - Watchdog timer
 * - Robust connection management
 */

// TINY_GSM_MODEM_SIM800 is defined in build_flags in platformio.ini
#define TINY_GSM_RX_BUFFER 1024
// #define DUMP_AT_COMMANDS  // Uncomment for AT command debugging

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "TinyGsmClient.h"
// #include "SparkFunBME280.h"  // Optional: Uncomment if using BME280 sensor
#include "config.h"
#include "passwords.h"
#include "esp_task_wdt.h"

#ifdef OTA_ENABLED
#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#endif

// Hardware Serial for SIM800 (must be declared before modem initialization)
HardwareSerial serialGsm(1);
#define SerialAT serialGsm

#ifdef DUMP_AT_COMMANDS
#include "StreamDebugger.h"
StreamDebugger debugger(serialGsm, Serial);
TinyGsm modem(debugger);
#else
TinyGsm modem(serialGsm);
#endif

// RTC memory for reset detection
RTC_DATA_ATTR int bootCount = 0;
RTC_DATA_ATTR unsigned long lastResetTime = 0;
RTC_DATA_ATTR bool wasRunning = false;

// MQTT Client
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// State variables
bool modemConnected = false;
bool wifiConnected = false;
bool mqttConnected = false;
bool lastMqttConnected = false; // Track previous MQTT connection state
bool gsmInitialized = false;
String smsNumber = "";
String smsText = "";
bool smsReceived = false;
bool smsSent = false;

// Device Watchdog
struct WatchdogDevice {
    String name;
    unsigned long interval;
    unsigned long lastHeartbeat;
    bool isOnline;
    bool isActive;
};
WatchdogDevice watchdogDevices[MAX_WATCHDOG_DEVICES];
unsigned long lastWatchdogCheck = 0;

// Connection tracking
unsigned long lastWifiCheck = 0;
unsigned long lastStatusPublish = 0;
unsigned long lastMqttAttempt = 0;
int wifiReconnectAttempts = 0;
int mqttReconnectAttempts = 0;

// OTA state
#ifdef OTA_ENABLED
bool otaEnabled = false;
bool otaInProgress = false;
unsigned long otaStartTime = 0;
#endif

// BME280 sensor (optional - not currently used)
// To enable BME280 support:
// 1. Uncomment the library in platformio.ini
// 2. Uncomment the include and variable below
// #include "SparkFunBME280.h"
// BME280 mySensor;
bool isEnvSensor = false;

// Emergency notification phone number (set in passwords.h)
// If not defined in passwords.h, define it here as empty string
#ifndef EMERGENCY_PHONE_NUMBER
#define EMERGENCY_PHONE_NUMBER ""
#endif

// Helper function to check if emergency SMS is enabled
bool isEmergencySMSEnabled() {
    return EMERGENCY_SMS_ENABLED && strlen(EMERGENCY_PHONE_NUMBER) > 0;
}

// Forward declarations
void publishWatchdogStatus();
void publishError(String errorType, String errorMessage);
String getTimestamp();
bool sendSMS(String phoneNumber, String message);

// Helper function to get emergency phone number as String
String getEmergencyPhoneNumber() {
    return String(EMERGENCY_PHONE_NUMBER);
}

/**
 * Initialize and power on GSM module
 */
bool GSM_ON(uint32_t time_delay) {
    Serial.println("[GSM] Initializing modem...");
    
    // Set-up modem reset, enable, power pins
    pinMode(MODEM_RST, OUTPUT);
    pinMode(MODEM_PWKEY, OUTPUT);
    pinMode(MODEM_POWER_ON, OUTPUT);

    Serial.println("[GSM] MODEM_RST & IP5306 IRQ: HIGH");
    digitalWrite(MODEM_RST, HIGH);
    delay(time_delay);

    Serial.println("[GSM] MODEM_PWKEY: HIGH");
    digitalWrite(MODEM_PWKEY, HIGH); // turning modem OFF
    delay(time_delay);

    Serial.println("[GSM] MODEM_POWER_ON: HIGH");
    digitalWrite(MODEM_POWER_ON, HIGH); // Enabling SY8089 4V4 for SIM800
    delay(time_delay);

    Serial.println("[GSM] MODEM_PWKEY: LOW");
    digitalWrite(MODEM_PWKEY, LOW); // turning modem ON
    delay(time_delay * 2); // Extra delay for modem to initialize
    
    // Set GSM module baud rate and UART pins
    SerialAT.begin(SERIAL_GSM_BAUD, SERIAL_8N1, MODEM_RX, MODEM_TX);
    delay(2000); // Wait for serial to stabilize
    
    // Test modem communication
    Serial.println("[GSM] Testing modem communication...");
    delay(1000);
    
    // Try to get modem info
    String modemInfo = modem.getModemInfo();
    if (modemInfo.length() > 0) {
        Serial.print("[GSM] Modem detected: ");
        Serial.println(modemInfo);
        gsmInitialized = true;
        return true;
    } else {
        Serial.println("[GSM] ERROR: Modem not responding!");
        gsmInitialized = false;
        return false;
    }
}

// Forward declarations for SMS functions
String readSMS(int index);
String getSenderID(int index);
int newMessageIndex(int startIndex);
bool deleteSMS(int index);

/**
 * Delete SMS message by index using AT command
 */
bool deleteSMS(int index) {
    if (index <= 0 || !gsmInitialized) return false;
    
    SerialAT.print("AT+CMGD=");
    SerialAT.print(index);
    SerialAT.print(",0\r");  // Delete without confirmation
    delay(500);
    
    // Wait for OK response
    String response = "";
    unsigned long startTime = millis();
    while (millis() - startTime < 2000) {
        if (SerialAT.available()) {
            char c = SerialAT.read();
            response += c;
            if (response.indexOf("OK") >= 0) {
                return true;
            }
            if (response.indexOf("ERROR") >= 0) {
                return false;
            }
        }
    }
    return false;
}

/**
 * Clear all SMS messages from buffer
 * Uses AT+CMGDA command to delete all messages at once (if supported)
 * Falls back to individual deletion if needed
 */
void clearSMSBuffer() {
    if (!gsmInitialized) return;
    
    Serial.println("[GSM] Clearing SMS buffer...");
    
    // Try to delete all SMS messages at once using AT+CMGDA
    SerialAT.print("AT+CMGDA=\"DEL ALL\"\r");
    delay(1000);
    
    // Check response
    String response = "";
    unsigned long startTime = millis();
    while (millis() - startTime < 3000) {
        if (SerialAT.available()) {
            char c = SerialAT.read();
            response += c;
            if (response.indexOf("OK") >= 0) {
                Serial.println(" All SMS messages deleted");
                return;
            }
            if (response.indexOf("ERROR") >= 0) {
                // AT+CMGDA not supported, try individual deletion
                break;
            }
        }
    }
    
    // Fallback: Delete messages individually
    Serial.print(" Using individual deletion");
    int deletedCount = 0;
    int maxAttempts = 20; // Limit to prevent infinite loop
    
    for (int i = 1; i <= maxAttempts; i++) {
        // Check if message exists by trying to read it
        String testSMS = readSMS(i);
        if (testSMS.length() > 0) {
            if (deleteSMS(i)) {
                deletedCount++;
                Serial.print(".");
            } else {
                break; // No more messages or error
            }
        } else {
            break; // No more messages
        }
        delay(200); // Small delay between deletions
    }
    
    if (deletedCount > 0) {
        Serial.print(" Cleared ");
        Serial.print(deletedCount);
        Serial.println(" messages");
    } else {
        Serial.println(" No messages to clear");
    }
}

/**
 * Power off GSM module
 */
void GSM_OFF() {
    Serial.println("[GSM] Powering off modem...");
    pinMode(MODEM_PWKEY, OUTPUT);
    pinMode(MODEM_POWER_ON, OUTPUT);
    pinMode(MODEM_RST, OUTPUT);

    digitalWrite(MODEM_PWKEY, HIGH); // turn off modem
    digitalWrite(MODEM_POWER_ON, LOW); // turn off modem PSU
    digitalWrite(MODEM_RST, HIGH); // Keep IRQ high
    gsmInitialized = false;
    modemConnected = false;
}

/**
 * Get current timestamp string
 */
String getTimestamp() {
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        return "N/A";
    }
    
    char currentTime[50];
    strftime(currentTime, 50, "%Y-%m-%dT%H:%M:%S%z", &timeinfo);
    return String(currentTime);
}

/**
 * Publish timestamp to MQTT
 */
void publishTimestamp(const char* topic) {
    if (!mqttConnected) return;
    
    String timestamp = getTimestamp();
    mqttClient.publish(topic, timestamp.c_str());
}

/**
 * Read SMS message by index using AT+CMGR command
 * Returns the SMS text, or empty string on error
 */
String readSMS(int index) {
    if (index <= 0 || !gsmInitialized) return "";
    
    // Set SMS to text mode if not already
    SerialAT.print("AT+CMGF=1\r");
    delay(500);
    while (SerialAT.available()) SerialAT.read(); // Clear buffer
    
    // Read SMS at index
    SerialAT.print("AT+CMGR=");
    SerialAT.print(index);
    SerialAT.print("\r");
    delay(1000);
    
    // Read response
    String response = "";
    unsigned long startTime = millis();
    while (millis() - startTime < 5000) {
        if (SerialAT.available()) {
            char c = SerialAT.read();
            response += c;
            if (response.indexOf("OK") >= 0 || response.indexOf("ERROR") >= 0) {
                break;
            }
        }
    }
    
    // Parse SMS text from response
    // Format: +CMGR: "REC UNREAD","+1234567890","","22/01/25,15:30:00+00"\r\n<message text>\r\nOK
    int textStart = response.indexOf("\r\n");
    if (textStart >= 0) {
        textStart += 2; // Skip \r\n
        int textEnd = response.lastIndexOf("\r\nOK");
        if (textEnd > textStart) {
            return response.substring(textStart, textEnd);
        }
    }
    
    return "";
}

/**
 * Get sender phone number from SMS at index using AT+CMGR command
 * Returns the phone number, or empty string on error
 */
String getSenderID(int index) {
    if (index <= 0 || !gsmInitialized) return "";
    
    // Set SMS to text mode if not already
    SerialAT.print("AT+CMGF=1\r");
    delay(500);
    while (SerialAT.available()) SerialAT.read(); // Clear buffer
    
    // Read SMS at index
    SerialAT.print("AT+CMGR=");
    SerialAT.print(index);
    SerialAT.print("\r");
    delay(1000);
    
    // Read response
    String response = "";
    unsigned long startTime = millis();
    while (millis() - startTime < 5000) {
        if (SerialAT.available()) {
            char c = SerialAT.read();
            response += c;
            if (response.indexOf("OK") >= 0 || response.indexOf("ERROR") >= 0) {
                break;
            }
        }
    }
    
    // Parse sender from response
    // Format: +CMGR: "REC UNREAD","+1234567890","","22/01/25,15:30:00+00"
    int senderStart = response.indexOf("\",\"");
    if (senderStart >= 0) {
        senderStart += 3; // Skip ",""
        int senderEnd = response.indexOf("\",\"", senderStart);
        if (senderEnd > senderStart) {
            return response.substring(senderStart, senderEnd);
        }
    }
    
    return "";
}

/**
 * Find index of new/unread SMS message
 * Uses AT+CMGL to list messages and finds first unread one
 * Returns message index (>0) if found, 0 if none
 */
int newMessageIndex(int startIndex) {
    if (!gsmInitialized) return 0;
    
    // Set SMS to text mode
    SerialAT.print("AT+CMGF=1\r");
    delay(500);
    while (SerialAT.available()) SerialAT.read(); // Clear buffer
    
    // List all unread messages (status "REC UNREAD")
    SerialAT.print("AT+CMGL=\"REC UNREAD\"\r");
    delay(1000);
    
    // Read response
    String response = "";
    unsigned long startTime = millis();
    while (millis() - startTime < 5000) {
        if (SerialAT.available()) {
            char c = SerialAT.read();
            response += c;
            if (response.indexOf("OK") >= 0 || response.indexOf("ERROR") >= 0) {
                break;
            }
        }
    }
    
    // Parse first message index from response
    // Format: +CMGL: <index>,"REC UNREAD","+1234567890",...
    int cmglPos = response.indexOf("+CMGL:");
    if (cmglPos >= 0) {
        cmglPos += 7; // Skip "+CMGL: "
        int commaPos = response.indexOf(",", cmglPos);
        if (commaPos > cmglPos) {
            String indexStr = response.substring(cmglPos, commaPos);
            int index = indexStr.toInt();
            if (index > 0) {
                return index;
            }
        }
    }
    
    return 0;
}

/**
 * Send SMS via GSM modem (with error handling)
 */
bool sendSMS(String phoneNumber, String message) {
    if (!gsmInitialized) {
        Serial.println("[SMS] ERROR: GSM not initialized!");
        return false;
    }
    
    Serial.print("[SMS] Sending to ");
    Serial.print(phoneNumber);
    Serial.print(": ");
    Serial.println(message);
    
    // Check if modem is ready
    if (!modem.testAT()) {
        Serial.println("[SMS] ERROR: Modem not responding to AT commands");
        return false;
    }
    
    // Wait for network registration
    Serial.println("[SMS] Waiting for network...");
    unsigned long networkStart = millis();
    while (!modem.waitForNetwork(5000)) {
        if (millis() - networkStart > GSM_NETWORK_WAIT_TIMEOUT) {
            Serial.println("[SMS] ERROR: Network registration timeout");
            return false;
        }
        Serial.print(".");
    }
    Serial.println(" OK");
    
    // Send SMS
    bool result = modem.sendSMS(phoneNumber, message);
    
    if (result) {
        Serial.println("[SMS] SMS sent successfully");
    } else {
        Serial.println("[SMS] ERROR: Failed to send SMS");
    }
    
    return result;
}

/**
 * Setup WiFi connection with timeout and retries
 */
bool setup_wifi() {
    Serial.println();
    Serial.print("[WiFi] Connecting to ");
    Serial.println(ssid);

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    unsigned long startTime = millis();
    int attempts = 0;
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        
        // Check timeout
        if (millis() - startTime > WIFI_CONNECT_TIMEOUT) {
            Serial.println();
            Serial.println("[WiFi] ERROR: Connection timeout!");
            wifiConnected = false;
            return false;
        }
        
        // Check for too many attempts
        attempts++;
        if (attempts > 100) { // 50 seconds max
            Serial.println();
            Serial.println("[WiFi] ERROR: Too many connection attempts!");
            wifiConnected = false;
            return false;
        }
    }

    Serial.println();
    Serial.println("[WiFi] Connected!");
    Serial.print("[WiFi] IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("[WiFi] RSSI: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    
    wifiConnected = true;
    wifiReconnectAttempts = 0;
    return true;
}

/**
 * Check and reconnect WiFi if needed
 */
bool checkAndReconnectWiFi() {
    if (WiFi.status() == WL_CONNECTED) {
        if (!wifiConnected) {
            Serial.println("[WiFi] Reconnected!");
            wifiConnected = true;
            wifiReconnectAttempts = 0;
        }
        return true;
    }
    
    // WiFi disconnected
    if (wifiConnected) {
        Serial.println("[WiFi] WARNING: Connection lost!");
        wifiConnected = false;
    }
    
    // Attempt reconnection
    if (wifiReconnectAttempts < WIFI_RECONNECT_ATTEMPTS) {
        Serial.print("[WiFi] Attempting reconnection (");
        Serial.print(wifiReconnectAttempts + 1);
        Serial.print("/");
        Serial.print(WIFI_RECONNECT_ATTEMPTS);
        Serial.println(")...");
        
        wifiReconnectAttempts++;
        bool success = setup_wifi();
        
        if (success) {
            // Notify via SMS if emergency number is set
            if (isEmergencySMSEnabled()) {
                String message = "SMS Gateway: WiFi reconnected after failure. IP: " + WiFi.localIP().toString();
                sendSMS(getEmergencyPhoneNumber(), message);
            }
            return true;
        }
    } else {
        // Max attempts reached - send emergency SMS
        if (isEmergencySMSEnabled() && gsmInitialized) {
            Serial.println("[WiFi] CRITICAL: WiFi unavailable - sending emergency SMS");
            String message = "SMS Gateway ALERT: WiFi unavailable! Device running on GSM only. Attempts: " + String(wifiReconnectAttempts);
            sendSMS(getEmergencyPhoneNumber(), message);
            // Reset counter to avoid spam
            wifiReconnectAttempts = 0;
        }
    }
    
    return false;
}

/**
 * MQTT message callback
 */
void mqttCallback(char* topic, byte* message, unsigned int length) {
    Serial.print("[MQTT] Message on topic: ");
    Serial.print(topic);
    Serial.print(": ");
    
    String messageTemp;
    for (int i = 0; i < length; i++) {
        Serial.print((char)message[i]);
        messageTemp += (char)message[i];
    }
    Serial.println();

    // Check if this is a send command
    if (String(topic) == String(MQTT_TOPIC_COMMAND_SEND)) {
        // Parse JSON payload
        StaticJsonDocument<512> doc;
        DeserializationError error = deserializeJson(doc, messageTemp);
        
        if (error) {
            Serial.print("[MQTT] ERROR: JSON parsing failed: ");
            Serial.println(error.c_str());
            return;
        }

        // Extract phone number and message text
        if (doc.containsKey("to") && doc.containsKey("text")) {
            smsNumber = doc["to"].as<String>();
            
            // Add '+' prefix if missing (stripped by Node-RED for MQTT compatibility)
            if (smsNumber.length() > 0 && smsNumber.charAt(0) != '+') {
                smsNumber = "+" + smsNumber;
            }
            
            smsText = doc["text"].as<String>();
            
            Serial.print("[MQTT] Sending SMS to: ");
            Serial.println(smsNumber);
            
            // Send SMS via modem
            bool result = sendSMS(smsNumber, smsText);
            
            // Publish response
            StaticJsonDocument<256> response;
            response["success"] = result;
            response["to"] = smsNumber;
            response["timestamp"] = getTimestamp();
            
            char responseBuffer[256];
            serializeJson(response, responseBuffer);
            
            if (mqttConnected) {
                mqttClient.publish(MQTT_TOPIC_SEND_RESPONSE, responseBuffer);
                publishTimestamp(MQTT_TOPIC_SEND_TIMESTAMP);
            }
            
            smsSent = true;
        } else {
            Serial.println("[MQTT] ERROR: Invalid JSON - missing 'to' or 'text' field");
        }
    }
    
    // Watchdog: Enroll/Update
    else if (String(topic) == String(MQTT_TOPIC_WATCHDOG_ENROLL)) {
        StaticJsonDocument<256> doc;
        if (deserializeJson(doc, messageTemp) == DeserializationError::Ok && doc.containsKey("name")) {
            String name = doc["name"].as<String>();
            unsigned long interval = doc["interval"] | 60;
            
            bool found = false;
            int emptyIdx = -1;
            for (int i = 0; i < MAX_WATCHDOG_DEVICES; i++) {
                if (watchdogDevices[i].isActive && watchdogDevices[i].name == name) {
                    watchdogDevices[i].interval = interval;
                    found = true;
                    String msg = "Watchdog: Device [" + name + "] updated. Interval: " + String(interval) + "s";
                    Serial.println("[WATCHDOG] " + msg);
                    if (isEmergencySMSEnabled() && gsmInitialized) sendSMS(getEmergencyPhoneNumber(), msg);
                    publishWatchdogStatus();
                    break;
                }
                if (!watchdogDevices[i].isActive && emptyIdx == -1) emptyIdx = i;
            }
            
            if (!found && emptyIdx != -1) {
                watchdogDevices[emptyIdx].name = name;
                watchdogDevices[emptyIdx].interval = interval;
                watchdogDevices[emptyIdx].lastHeartbeat = millis();
                watchdogDevices[emptyIdx].isOnline = false;
                watchdogDevices[emptyIdx].isActive = true;
                String msg = "Watchdog: Device [" + name + "] enrolled. Interval: " + String(interval) + "s";
                Serial.println("[WATCHDOG] " + msg);
                if (isEmergencySMSEnabled() && gsmInitialized) sendSMS(getEmergencyPhoneNumber(), msg);
                publishWatchdogStatus();
            }
        }
    }
    // Watchdog: Delete
    else if (String(topic) == String(MQTT_TOPIC_WATCHDOG_DELETE)) {
        StaticJsonDocument<128> doc;
        if (deserializeJson(doc, messageTemp) == DeserializationError::Ok && doc.containsKey("name")) {
            String name = doc["name"].as<String>();
            Serial.print("[WATCHDOG] Delete request for: ");
            Serial.println(name);
            for (int i = 0; i < MAX_WATCHDOG_DEVICES; i++) {
                if (watchdogDevices[i].isActive && watchdogDevices[i].name == name) {
                    watchdogDevices[i].isActive = false;
                    String msg = "Watchdog: Device [" + name + "] deleted and unmonitored.";
                    Serial.println("[WATCHDOG] " + msg);
                    if (isEmergencySMSEnabled() && gsmInitialized) sendSMS(getEmergencyPhoneNumber(), msg);
                    publishWatchdogStatus();
                    break;
                }
            }
        }
    }
    // Watchdog: Heartbeat
    else if (String(topic) == String(MQTT_TOPIC_WATCHDOG_HEARTBEAT)) {
        StaticJsonDocument<128> doc;
        if (deserializeJson(doc, messageTemp) == DeserializationError::Ok && doc.containsKey("name")) {
            String name = doc["name"].as<String>();
            for (int i = 0; i < MAX_WATCHDOG_DEVICES; i++) {
                if (watchdogDevices[i].isActive && watchdogDevices[i].name == name) {
                    watchdogDevices[i].lastHeartbeat = millis();
                    Serial.print("[WATCHDOG] Heartbeat from: ");
                    Serial.println(name);
                    if (!watchdogDevices[i].isOnline) {
                        watchdogDevices[i].isOnline = true;
                        String msg = "Watchdog: Device [" + name + "] is ONLINE/CONNECTED";
                        Serial.println("[WATCHDOG] " + msg);
                        if (isEmergencySMSEnabled() && gsmInitialized) sendSMS(getEmergencyPhoneNumber(), msg);
                    }
                    publishWatchdogStatus();
                    break;
                }
            }
        }
    }
    
#ifdef OTA_ENABLED
    // Check if this is an OTA command
    else if (String(topic) == String(MQTT_TOPIC_OTA_COMMAND)) {
        // Parse JSON payload
        StaticJsonDocument<256> doc;
        DeserializationError error = deserializeJson(doc, messageTemp);
        
        if (error) {
            Serial.print("[OTA] ERROR: JSON parsing failed: ");
            Serial.println(error.c_str());
            return;
        }
        
        String action = doc["action"].as<String>();
        
        if (action == "enable") {
            Serial.println("[OTA] OTA enabled via MQTT command");
            otaEnabled = true;
            
            // Publish status
            if (mqttConnected) {
                StaticJsonDocument<128> status;
                status["enabled"] = true;
                status["message"] = "OTA enabled";
                status["timestamp"] = getTimestamp();
                
                char buffer[128];
                serializeJson(status, buffer);
                mqttClient.publish(MQTT_TOPIC_OTA_STATUS, buffer);
            }
        } else if (action == "disable") {
            Serial.println("[OTA] OTA disabled via MQTT command");
            otaEnabled = false;
            otaInProgress = false;
            
            // Publish status
            if (mqttConnected) {
                StaticJsonDocument<128> status;
                status["enabled"] = false;
                status["message"] = "OTA disabled";
                status["timestamp"] = getTimestamp();
                
                char buffer[128];
                serializeJson(status, buffer);
                mqttClient.publish(MQTT_TOPIC_OTA_STATUS, buffer);
            }
        }
    }
#endif
}

/**
 * Reconnect to MQTT broker with retries
 */
bool reconnectMQTT() {
    if (mqttClient.connected()) {
        mqttConnected = true;
        mqttReconnectAttempts = 0;
        return true;
    }
    
    // Check if WiFi is available
    if (!wifiConnected || WiFi.status() != WL_CONNECTED) {
        Serial.println("[MQTT] ERROR: WiFi not connected, cannot connect to MQTT");
        return false;
    }
    
    // Rate limit reconnection attempts
    if (millis() - lastMqttAttempt < MQTT_RECONNECT_DELAY) {
        return false;
    }
    lastMqttAttempt = millis();
    
    Serial.print("[MQTT] Attempting connection");
    if (mqttReconnectAttempts > 0) {
        Serial.print(" (attempt ");
        Serial.print(mqttReconnectAttempts + 1);
        Serial.print("/");
        Serial.print(MQTT_RECONNECT_ATTEMPTS);
        Serial.print(")");
    }
    Serial.println("...");
    
    // Attempt to connect with credentials
    bool connected = false;
    if (strlen(mqtt_username) > 0 && strlen(mqtt_password) > 0) {
        connected = mqttClient.connect(mqtt_client_id, mqtt_username, mqtt_password);
    } else {
        connected = mqttClient.connect(mqtt_client_id);
    }
    
    if (connected) {
        Serial.println("[MQTT] Connected!");
        mqttConnected = true;
        mqttReconnectAttempts = 0;
        
        // Subscribe to command topics
        if (mqttClient.subscribe(MQTT_TOPIC_COMMAND_SEND)) {
            Serial.println("[MQTT] Subscribed to command SEND");
        } else {
            Serial.println("[MQTT] ERROR: Failed to subscribe to command SEND");
        }

        if (mqttClient.subscribe(MQTT_TOPIC_WATCHDOG_ENROLL)) {
            Serial.println("[MQTT] Subscribed to Watchdog ENROLL");
        } else {
            Serial.println("[MQTT] ERROR: Failed to subscribe to Watchdog ENROLL");
        }

        if (mqttClient.subscribe(MQTT_TOPIC_WATCHDOG_DELETE)) {
            Serial.println("[MQTT] Subscribed to Watchdog DELETE");
        } else {
            Serial.println("[MQTT] ERROR: Failed to subscribe to Watchdog DELETE");
        }

        if (mqttClient.subscribe(MQTT_TOPIC_WATCHDOG_HEARTBEAT)) {
            Serial.println("[MQTT] Subscribed to Watchdog HEARTBEAT");
        } else {
            Serial.println("[MQTT] ERROR: Failed to subscribe to Watchdog HEARTBEAT");
        }
        
        Serial.println("[MQTT] Subscription process complete");
        
        // Publish initial status
        publishTimestamp(MQTT_TOPIC_STATUS);
        
        // Notify via SMS if reconnected after failure
        if (isEmergencySMSEnabled() && gsmInitialized) {
            String message = "SMS Gateway: MQTT connection restored. Device back online.";
            sendSMS(getEmergencyPhoneNumber(), message);
        }
        
        return true;
    } else {
        Serial.print("[MQTT] ERROR: Connection failed, rc=");
        Serial.print(mqttClient.state());
        Serial.println();
        
        mqttReconnectAttempts++;
        mqttConnected = false;
        
        // If max attempts reached, send SMS notification
        if (mqttReconnectAttempts >= MQTT_RECONNECT_ATTEMPTS && 
            isEmergencySMSEnabled() && 
            gsmInitialized) {
            Serial.println("[MQTT] CRITICAL: MQTT unavailable - sending emergency SMS");
            String message = "SMS Gateway ALERT: MQTT broker unavailable! Attempts: " + String(mqttReconnectAttempts);
            sendSMS(getEmergencyPhoneNumber(), message);
            mqttReconnectAttempts = 0; // Reset to avoid spam
        }
        
        return false;
    }
}

/**
 * Publish reset announcement to MQTT
 */
void announceReset() {
    if (!mqttConnected) {
        Serial.println("[RESET] MQTT not connected, cannot announce reset");
        return;
    }
    
    StaticJsonDocument<256> resetInfo;
    resetInfo["boot_count"] = bootCount;
    resetInfo["reset_type"] = (bootCount == 1) ? "cold_boot" : "watchdog_reset";
    resetInfo["timestamp"] = getTimestamp();
    resetInfo["last_reset_time"] = (lastResetTime > 0) ? lastResetTime : 0;
    resetInfo["was_running"] = wasRunning;
    
    char buffer[256];
    serializeJson(resetInfo, buffer);
    
    if (mqttClient.publish(MQTT_TOPIC_RESET, buffer)) {
        Serial.println("[RESET] Reset announcement published to MQTT");
    } else {
        Serial.println("[RESET] ERROR: Failed to publish reset announcement");
    }
}

/**
 * Publish error to MQTT
 */
void publishError(String errorType, String errorMessage) {
    if (!mqttConnected) return;
    
    StaticJsonDocument<256> errorInfo;
    errorInfo["type"] = errorType;
    errorInfo["message"] = errorMessage;
    errorInfo["timestamp"] = getTimestamp();
    
    char buffer[256];
    serializeJson(errorInfo, buffer);
    
    mqttClient.publish(MQTT_TOPIC_ERROR, buffer);
    
    // Notify via SMS if emergency number is set
    if (isEmergencySMSEnabled() && gsmInitialized) {
        String smsMessage = "SMS Gateway EXCEPTION: [" + errorType + "] " + errorMessage;
        sendSMS(getEmergencyPhoneNumber(), smsMessage);
    }
}

/**
 * Publish watchdog status to MQTT
 */
void publishWatchdogStatus() {
    if (!mqttConnected) return;
    
    Serial.println("[WATCHDOG] Publishing status...");
    StaticJsonDocument<1024> doc;
    JsonArray array = doc.to<JsonArray>();
    
    unsigned long now = millis();
    for (int i = 0; i < MAX_WATCHDOG_DEVICES; i++) {
        if (watchdogDevices[i].isActive) {
            JsonObject device = array.createNestedObject();
            device["name"] = watchdogDevices[i].name;
            device["interval"] = watchdogDevices[i].interval;
            device["online"] = watchdogDevices[i].isOnline;
            device["age"] = (now - watchdogDevices[i].lastHeartbeat) / 1000;
        }
    }
    
    char buffer[1024];
    serializeJson(doc, buffer);
    if (mqttClient.publish(MQTT_TOPIC_WATCHDOG_STATUS, buffer)) {
        Serial.println("[WATCHDOG] Status published successfully");
    } else {
        Serial.println("[WATCHDOG] ERROR: Failed to publish status");
    }
}

#ifdef OTA_ENABLED
/**
 * Initialize OTA (Over-The-Air) update capability
 */
void setupOTA() {
    Serial.println("[OTA] Initializing OTA...");
    
    // Set hostname
    ArduinoOTA.setHostname(OTA_HOSTNAME);
    
    // Set password if configured (from passwords.h)
    #ifndef OTA_PASSWORD
    #define OTA_PASSWORD ""
    #endif
    if (strlen(OTA_PASSWORD) > 0) {
        ArduinoOTA.setPassword(OTA_PASSWORD);
        Serial.println("[OTA] Password protection enabled");
    } else {
        Serial.println("[OTA] WARNING: No password set - OTA is unsecured!");
    }
    
    // OTA start callback
    ArduinoOTA.onStart([]() {
        String type;
        if (ArduinoOTA.getCommand() == U_FLASH) {
            type = "sketch";
        } else { // U_SPIFFS
            type = "filesystem";
        }
        
        Serial.println("[OTA] Start updating " + type);
        otaInProgress = true;
        otaStartTime = millis();
        
        // Publish OTA start status
        if (mqttConnected) {
            StaticJsonDocument<128> status;
            status["status"] = "started";
            status["type"] = type;
            status["timestamp"] = getTimestamp();
            
            char buffer[128];
            serializeJson(status, buffer);
            mqttClient.publish(MQTT_TOPIC_OTA_STATUS, buffer);
        }
        
        // Send SMS notification if enabled
        if (isEmergencySMSEnabled() && gsmInitialized) {
            String message = "SMS Gateway: OTA update started (" + type + "). Device will reboot after update.";
            sendSMS(getEmergencyPhoneNumber(), message);
        }
    });
    
    // OTA end callback
    ArduinoOTA.onEnd([]() {
        Serial.println("\n[OTA] End");
        otaInProgress = false;
        
        // Publish OTA end status
        if (mqttConnected) {
            StaticJsonDocument<128> status;
            status["status"] = "completed";
            status["duration_ms"] = millis() - otaStartTime;
            status["timestamp"] = getTimestamp();
            
            char buffer[128];
            serializeJson(status, buffer);
            mqttClient.publish(MQTT_TOPIC_OTA_STATUS, buffer);
        }
    });
    
    // OTA progress callback
    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        unsigned int percent = (progress / (total / 100));
        Serial.printf("[OTA] Progress: %u%%\r", percent);
        
        // Publish progress every 10%
        static unsigned int lastPercent = 0;
        if (percent >= lastPercent + 10) {
            lastPercent = percent;
            
            if (mqttConnected) {
                StaticJsonDocument<64> progressInfo;
                progressInfo["progress"] = percent;
                progressInfo["bytes"] = progress;
                progressInfo["total"] = total;
                
                char buffer[64];
                serializeJson(progressInfo, buffer);
                mqttClient.publish(MQTT_TOPIC_OTA_PROGRESS, buffer);
            }
        }
    });
    
    // OTA error callback
    ArduinoOTA.onError([](ota_error_t error) {
        Serial.printf("[OTA] Error[%u]: ", error);
        String errorMsg = "";
        
        if (error == OTA_AUTH_ERROR) {
            errorMsg = "Auth Failed";
        } else if (error == OTA_BEGIN_ERROR) {
            errorMsg = "Begin Failed";
        } else if (error == OTA_CONNECT_ERROR) {
            errorMsg = "Connect Failed";
        } else if (error == OTA_RECEIVE_ERROR) {
            errorMsg = "Receive Failed";
        } else if (error == OTA_END_ERROR) {
            errorMsg = "End Failed";
        }
        
        Serial.println(errorMsg);
        otaInProgress = false;
        
        // Publish error
        if (mqttConnected) {
            StaticJsonDocument<128> status;
            status["status"] = "error";
            status["error"] = errorMsg;
            status["error_code"] = error;
            status["timestamp"] = getTimestamp();
            
            char buffer[128];
            serializeJson(status, buffer);
            mqttClient.publish(MQTT_TOPIC_OTA_STATUS, buffer);
        }
        
        // Send SMS notification
        if (isEmergencySMSEnabled() && gsmInitialized) {
            String message = "SMS Gateway ALERT: OTA update failed! Error: " + errorMsg;
            sendSMS(getEmergencyPhoneNumber(), message);
        }
    });
    
    // Begin OTA
    ArduinoOTA.begin();
    otaEnabled = true;
    
    Serial.print("[OTA] Ready! Hostname: ");
    Serial.print(OTA_HOSTNAME);
    Serial.print(", Port: ");
    Serial.println(OTA_PORT);
    Serial.print("[OTA] IP address: ");
    Serial.println(WiFi.localIP());
}
#endif

/**
 * Setup function
 */
void setup() {
    // Initialize serial
    Serial.begin(SERIAL_DEBUG_BAUD);
    delay(1000);
    
    Serial.println();
    Serial.println("========================================");
    Serial.println("SMS Gateway Starting...");
    Serial.println("========================================");
    
    // Increment boot count
    bootCount++;
    wasRunning = (bootCount > 1);
    lastResetTime = millis();
    
    Serial.print("[BOOT] Boot count: ");
    Serial.println(bootCount);
    
    // Setup watchdog timer
    esp_task_wdt_init(WATCHDOG_TIMEOUT, true);
    esp_task_wdt_add(NULL);
    Serial.println("[BOOT] Watchdog timer enabled");
    
    // Initialize GSM module first (needed for emergency SMS)
    Serial.println("[BOOT] Initializing GSM module...");
    if (!GSM_ON(GSM_INIT_DELAY)) {
        Serial.println("[BOOT] WARNING: GSM initialization failed, continuing anyway...");
    } else {
        Serial.println("[BOOT] GSM module initialized");
    }
    
    // Wait a bit for GSM to stabilize
    delay(2000);
    
    // Setup WiFi
    Serial.println("[BOOT] Setting up WiFi...");
    if (!setup_wifi()) {
        Serial.println("[BOOT] ERROR: WiFi setup failed!");
        
        // Send emergency SMS if WiFi fails
        if (isEmergencySMSEnabled() && gsmInitialized) {
            Serial.println("[BOOT] Sending emergency SMS about WiFi failure...");
            String message = "SMS Gateway ALERT: WiFi connection failed on boot! Device may be offline.";
            sendSMS(getEmergencyPhoneNumber(), message);
        }
        
        // Continue anyway - might recover later
    }
    
    // Setup MQTT
    if (wifiConnected) {
        Serial.println("[BOOT] Setting up MQTT...");
        mqttClient.setServer(mqtt_server, mqtt_port);
        mqttClient.setCallback(mqttCallback);
        mqttClient.setKeepAlive(60);
        mqttClient.setSocketTimeout(5);
        
        // Attempt initial connection
        reconnectMQTT();
        
        // Subscribe to OTA command topic
        #ifdef OTA_ENABLED
        if (mqttConnected) {
            mqttClient.subscribe(MQTT_TOPIC_OTA_COMMAND);
            Serial.print("[BOOT] Subscribed to OTA command: ");
            Serial.println(MQTT_TOPIC_OTA_COMMAND);
        }
        
        // Setup OTA if WiFi is connected
        Serial.println("[BOOT] Setting up OTA...");
        setupOTA();
        #endif
    } else {
        Serial.println("[BOOT] Skipping MQTT setup - WiFi not connected");
    }
    
    // Initialize NTP for timestamps
    Serial.println("[BOOT] Configuring NTP...");
    configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);
    delay(2000); // Wait for NTP sync
    
    // Announce reset if MQTT is connected
    if (mqttConnected) {
        announceReset();
        publishTimestamp(MQTT_TOPIC_STATUS);
    } else if (gsmInitialized && isEmergencySMSEnabled()) {
        // Send SMS about reset if MQTT unavailable
        String message = "SMS Gateway: Device reset (boot #" + String(bootCount) + "). MQTT unavailable.";
        sendSMS(getEmergencyPhoneNumber(), message);
    }
    
    // Clear old SMS messages (optional - helps prevent buffer overflow)
    if (gsmInitialized) {
        clearSMSBuffer();
    }
    
    Serial.println("========================================");
    Serial.println("SMS Gateway Ready!");
    Serial.println("========================================");
    Serial.println();
    
    // Send "Device Online" SMS notification after successful initialization
    if (gsmInitialized && isEmergencySMSEnabled()) {
        Serial.println("[BOOT] Sending 'Device Online' SMS notification...");
        
        String message = "SMS Gateway: Device is ONLINE\n";
        message += "Boot #" + String(bootCount) + "\n";
        
        if (wifiConnected) {
            message += "WiFi: Connected\n";
            message += "IP: " + WiFi.localIP().toString() + "\n";
        } else {
            message += "WiFi: Disconnected\n";
        }
        
        if (mqttConnected) {
            message += "MQTT: Connected\n";
        } else {
            message += "MQTT: Disconnected\n";
        }
        
        message += "GSM: " + String(gsmInitialized ? "Ready" : "Not Ready");
        
        if (sendSMS(getEmergencyPhoneNumber(), message)) {
            Serial.println("[BOOT] 'Device Online' SMS sent successfully");
        } else {
            Serial.println("[BOOT] WARNING: Failed to send 'Device Online' SMS");
        }
    }
}

/**
 * Main loop
 */
void loop() {
    // Feed watchdog
    esp_task_wdt_reset();
    
    // Check WiFi connection
    unsigned long now = millis();
    if (now - lastWifiCheck > WIFI_CHECK_INTERVAL) {
        lastWifiCheck = now;
        checkAndReconnectWiFi();
    }
    
    // Maintain MQTT connection
    if (wifiConnected) {
        bool currentMqttConnected = mqttClient.connected();
        
        // Detect disconnect
        if (!currentMqttConnected && lastMqttConnected) {
            Serial.println("[MQTT] WARNING: Connection lost!");
            if (isEmergencySMSEnabled() && gsmInitialized) {
                String message = "SMS Gateway ALERT: MQTT connection lost! Attempting recovery...";
                sendSMS(getEmergencyPhoneNumber(), message);
            }
        }
        
        if (!currentMqttConnected) {
            reconnectMQTT();
        } else {
            mqttClient.loop();
        }
        
        lastMqttConnected = mqttClient.connected();
    }
    
    // Publish periodic status
    if (mqttConnected && (now - lastStatusPublish > STATUS_PUBLISH_INTERVAL)) {
        lastStatusPublish = now;
        publishTimestamp(MQTT_TOPIC_STATUS);
        
        // Publish connection status
        StaticJsonDocument<128> status;
        status["wifi"] = wifiConnected ? "connected" : "disconnected";
        status["mqtt"] = mqttConnected ? "connected" : "disconnected";
        status["gsm"] = gsmInitialized ? "initialized" : "not_initialized";
        status["timestamp"] = getTimestamp();
        
        char buffer[128];
        serializeJson(status, buffer);
        mqttClient.publish(MQTT_TOPIC_STATUS, buffer);
    }
    
    // Check for new SMS messages
    if (gsmInitialized) {
        int index = newMessageIndex(0);
        if (index > 0) {
            String SMS = readSMS(index);
            String ID = getSenderID(index);
            
            Serial.println("[SMS] New message received!");
            Serial.print("[SMS] From: ");
            Serial.println(ID);
            Serial.print("[SMS] Text: ");
            Serial.println(SMS);
            
            // Publish received SMS to MQTT
            if (mqttConnected) {
                mqttClient.publish(MQTT_TOPIC_RECEIVE_FROM, ID.c_str());
                mqttClient.publish(MQTT_TOPIC_RECEIVE_TEXT, SMS.c_str());
                publishTimestamp(MQTT_TOPIC_RECEIVE_TIMESTAMP);
            } else {
                Serial.println("[SMS] WARNING: MQTT not connected, SMS not published");
            }
            
            smsReceived = true;
            
            // Delete the SMS after reading (prevents buffer overflow)
            if (deleteSMS(index)) {
                Serial.println("[SMS] Message deleted from buffer");
            } else {
                Serial.println("[SMS] WARNING: Failed to delete message (may remain in buffer)");
            }
        }
    }
    
    // Check watchdog devices
    if (now - lastWatchdogCheck > 10000) { // Check every 10 seconds
        lastWatchdogCheck = now;
        for (int i = 0; i < MAX_WATCHDOG_DEVICES; i++) {
            if (watchdogDevices[i].isActive && watchdogDevices[i].isOnline) {
                if (now - watchdogDevices[i].lastHeartbeat > (watchdogDevices[i].interval * 2000)) {
                    watchdogDevices[i].isOnline = false;
                    String msg = "Watchdog ALERT: Device [" + watchdogDevices[i].name + "] connection LOST! Timeout: " + String(watchdogDevices[i].interval * 2) + "s";
                    Serial.println("[WATCHDOG] " + msg);
                    if (isEmergencySMSEnabled() && gsmInitialized) sendSMS(getEmergencyPhoneNumber(), msg);
                    
                    // Also publish error to MQTT
                    publishError("WatchdogTimeout", "Connection lost for " + watchdogDevices[i].name);
                    
                    publishWatchdogStatus();
                }
            }
        }
        
        // Always publish status periodically if check triggered
        publishWatchdogStatus();
    }
    
    // Small delay to prevent watchdog issues
    delay(100);
}
