import pika

# Set up connection parameters to RabbitMQ server
credentials = pika.PlainCredentials('agentia', '9puv4b8x2et')
parameters = pika.ConnectionParameters('rabbitserver20230418.westeurope.azurecontainer.io', 5672, '/', credentials)

# Callback function to print received messages
def callback(ch, method, properties, body):
    print("Received message:", body.decode())

# Establish a connection
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Set up callback function to handle incoming messages
channel.basic_consume(queue='stationData', on_message_callback=callback, auto_ack=True)

print('Waiting for messages. Press CTRL+C to exit.')

# Start consuming messages
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print('Disconnecting...')
    channel.stop_consuming()

connection.close()