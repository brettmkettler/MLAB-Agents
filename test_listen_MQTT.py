import paho.mqtt.client as mqtt
import logging

logging.basicConfig(level=logging.DEBUG)

# Connection configuration
connection_config = {
    "type": "MQTT",
    "isActive": True,
    "host": "68.221.122.91",
    "port": 1883,  # Adjust this if using SSL/TLS
    "path": "/",  # This is not used directly by paho-mqtt
    "user": "unityAgentMQTT",
    "password": "password",
    "isSecure": False,  # Adjust this to True if using SSL/TLS
    "topics": ["unityassemblyAgent", "unityQualityAgent", "unityMasterAgent"]
}

# Define the callback function for message reception
def on_message(client, userdata, msg):
    print(f"Received message '{msg.payload.decode()}' on topic '{msg.topic}'")

# Define the callback function for connection
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        # Subscribe to the specified topic
        topic_to_listen = connection_config["topics"][0]
        client.subscribe(topic_to_listen)
        print(f"Subscribed to topic {topic_to_listen}")
    else:
        print(f"Failed to connect, return code {rc}")

# Define the callback function for logging
def on_log(client, userdata, level, buf):
    print(f"Log: {buf}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback functions
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log

# Set username and password
client.username_pw_set(connection_config["user"], connection_config["password"])

# Enable SSL/TLS if required
if connection_config["isSecure"]:
    client.tls_set()

# Connect to the broker
client.connect(connection_config["host"], connection_config["port"], 60)

# Start the MQTT client loop to listen for messages
client.loop_forever()
