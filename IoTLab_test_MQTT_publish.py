import paho.mqtt.client as mqtt

username = "UnityAgent"
password = "mlab120!"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.publish("unity_assessment", "this is my test to unity_assessment")
    else:
        print("Connection error: " + str(rc))

def on_message(client, userdata, msg):
    print("New message from " + msg.topic + ": " + str(msg.payload.decode()))

if __name__ == "__main__":
    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    broker_address = "68.221.122.91"
    broker_port = 1883
    client.connect(broker_address, broker_port, 60)
    client.loop_forever()
