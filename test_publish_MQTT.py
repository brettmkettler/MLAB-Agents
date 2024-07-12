import paho.mqtt.client as mqtt
import logging
import ssl


logging.basicConfig(level=logging.DEBUG)

# Connection configuration
connection_config = {
    "type": "MQTT",
    "isActive": True,
    "host": "68.221.122.91",
    "port": 8883,  # Adjust this if using SSL/TLS
    "path": "/",  # This is not used directly by paho-mqtt
    "user": "AIAgent",
    "password": "mlab120!",
    "isSecure": True,  # Adjust this to True if using SSL/TLS
    "topics": ["unityAssessmentAgent", "unityQualityAgent", "unityMasterAgent"]
}

# Define the callback function for logging
def on_log(client, userdata, level, buf):
    print(f"Log: {buf}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback function
client.on_log = on_log

# Set username and password
client.username_pw_set(connection_config["user"], connection_config["password"])

# Enable SSL/TLS if required
if connection_config["isSecure"]:
    client.tls_set(cert_reqs=ssl.CERT_NONE)  # Disable SSL certificate verification

# Connect to the broker
client.connect(connection_config["host"], connection_config["port"], 60)

# Start the MQTT client loop
client.loop_start()

# Publish a test message to a specific topic
def publish_message():
    topic_to_publish = connection_config["topics"][0]
    message = "Hello from publish_mqtt.py ssl"
    client.publish(topic_to_publish, message)
    print(f"Published message '{message}' to topic '{topic_to_publish}'")

if __name__ == "__main__":
    publish_message()

    # Allow some time for the message to be sent
    import time
    time.sleep(2)

    # Stop the loop and disconnect
    client.loop_stop()
    client.disconnect()
