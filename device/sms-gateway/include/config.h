#ifndef CONFIG_H
#define CONFIG_H

// MQTT Topic Configuration
// Following project convention: {domain}/{location}/{device}/{type}/{action}
#define MQTT_TOPIC_PREFIX "sms/gateway"

// Command topics (subscribe to receive commands)
#define MQTT_TOPIC_COMMAND_SEND MQTT_TOPIC_PREFIX "/command/send"
#define MQTT_TOPIC_WATCHDOG_ENROLL MQTT_TOPIC_PREFIX "/watchdog/enroll"
#define MQTT_TOPIC_WATCHDOG_DELETE MQTT_TOPIC_PREFIX "/watchdog/delete"
#define MQTT_TOPIC_WATCHDOG_HEARTBEAT MQTT_TOPIC_PREFIX "/watchdog/heartbeat"

// Status topics (publish status updates)
#define MQTT_TOPIC_STATUS MQTT_TOPIC_PREFIX "/status"
#define MQTT_TOPIC_STATUS_TIMESTAMP MQTT_TOPIC_PREFIX "/status/timestamp"
#define MQTT_TOPIC_WATCHDOG_STATUS MQTT_TOPIC_PREFIX "/watchdog/status"

// Receive topics (publish received SMS)
#define MQTT_TOPIC_RECEIVE_FROM MQTT_TOPIC_PREFIX "/receive/from"
#define MQTT_TOPIC_RECEIVE_TEXT MQTT_TOPIC_PREFIX "/receive/text"
#define MQTT_TOPIC_RECEIVE_TIMESTAMP MQTT_TOPIC_PREFIX "/receive/timestamp"

// Send topics (publish sent SMS confirmation)
#define MQTT_TOPIC_SEND_TIMESTAMP MQTT_TOPIC_PREFIX "/send/timestamp"
#define MQTT_TOPIC_SEND_RESPONSE MQTT_TOPIC_PREFIX "/send/response"

// Legacy topic support (for backward compatibility)
// These can be enabled if needed for migration period
// #define ENABLE_LEGACY_TOPICS

// Hardware pin definitions for LilyGo T-Call SIM800
#define MODEM_RST 5      // SIM800 RESET & IP5306 IRQ
#define MODEM_PWKEY 4    // PWRKEY SIM800
#define MODEM_POWER_ON 23 // EN SY8089 4v4 regulator for SIM800
#define MODEM_TX 27
#define MODEM_RX 26
#define I2C_SDA 21
#define I2C_SCL 22
#define ADC_BAT 35       // Battery voltage ADC pin

// Serial configuration
#define SERIAL_DEBUG_BAUD 115200
#define SERIAL_GSM_BAUD 115200

// NTP configuration
#define NTP_SERVER "pool.ntp.org"
#define GMT_OFFSET_SEC 0
#define DAYLIGHT_OFFSET_SEC 3600

// Timing configuration
#define MQTT_RECONNECT_DELAY 5000  // milliseconds
#define SMS_BUFFER_CHECK_DELAY 1000  // milliseconds
#define WIFI_CONNECT_TIMEOUT 30000  // milliseconds (30 seconds)
#define WIFI_RECONNECT_ATTEMPTS 3
#define MQTT_RECONNECT_ATTEMPTS 5
#define GSM_INIT_DELAY 1000  // milliseconds
#define GSM_NETWORK_WAIT_TIMEOUT 60000  // milliseconds (60 seconds)
#define WATCHDOG_TIMEOUT 60  // seconds
#define STATUS_PUBLISH_INTERVAL 300000  // milliseconds (5 minutes)
#define WIFI_CHECK_INTERVAL 60000  // milliseconds (1 minute)
#define MAX_WATCHDOG_DEVICES 10   // Maximum number of monitored devices

// Emergency SMS notification (sent when WiFi fails)
// Phone number should be set in passwords.h
#define EMERGENCY_SMS_ENABLED true

// Reset announcement
#define MQTT_TOPIC_RESET MQTT_TOPIC_PREFIX "/reset"
#define MQTT_TOPIC_ERROR MQTT_TOPIC_PREFIX "/error"

// OTA update topics
#define MQTT_TOPIC_OTA_COMMAND MQTT_TOPIC_PREFIX "/command/ota"
#define MQTT_TOPIC_OTA_STATUS MQTT_TOPIC_PREFIX "/ota/status"
#define MQTT_TOPIC_OTA_PROGRESS MQTT_TOPIC_PREFIX "/ota/progress"

// OTA configuration
#define OTA_PORT 3232
#define OTA_HOSTNAME "esp32-sms-gateway"
// OTA_PASSWORD is defined in passwords.h

#endif
