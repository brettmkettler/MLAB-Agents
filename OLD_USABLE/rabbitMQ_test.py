import pika

# Connection parameters
credentials = pika.PlainCredentials('AIAgent', 'mlab120!')
parameters = pika.ConnectionParameters('68.221.122.91',
                                       5672,
                                       '/',
                                       credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declare a queue
# channel.queue_declare(queue='test_queue')

# Publish a message to the queue
channel.basic_publish(exchange='',
                      routing_key='test_queue',
                      body='Hello, Ash!')
print(" [x] Sent 'Hello, Ash!'")

# Define a callback to handle messages from the queue
def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

# Consume messages from the queue
channel.basic_consume(queue='test_queue',
                      on_message_callback=callback,
                      auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
