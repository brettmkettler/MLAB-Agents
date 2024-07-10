import pika
import json
import time
from threading import Thread
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Agent:
    def __init__(self, name, exchange, routing_key, queue, user, password):
        self.name = name
        self.exchange = exchange
        self.routing_key = routing_key
        self.queue = queue
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST'),
                port=int(os.getenv('RABBITMQ_PORT')),
                credentials=pika.PlainCredentials(user, password)
            )
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct')
        self.channel.queue_declare(queue=self.queue, durable=True)
        self.channel.queue_bind(exchange=self.exchange, queue=self.queue, routing_key=self.routing_key)

    def send_message(self, message, target_routing_key):
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=target_routing_key,
            body=json.dumps({'sender': self.name, 'message': message}),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                timestamp=int(time.time())
            )
        )
        self.log_message(f"Sent: {message}")

    def receive_messages(self):
        def callback(ch, method, properties, body):
            message = json.loads(body)
            self.log_message(f"Received from {message['sender']}: {message['message']}")
            self.process_message(message)

        self.channel.basic_consume(queue=self.queue, on_message_callback=callback, auto_ack=True)
        print(f"[{self.name}] Waiting for messages...")
        self.channel.start_consuming()

    

    def log_message(self, message):
        self.channel.basic_publish(
            exchange='log_exchange',
            routing_key='log',
            body=json.dumps({'agent': self.name, 'log': message}),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make log message persistent
                timestamp=int(time.time())
            )
        )

    def start_receiving(self):
        thread = Thread(target=self.receive_messages)
        thread.start()
