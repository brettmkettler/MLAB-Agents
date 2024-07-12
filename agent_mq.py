import pika
import json
from dotenv import load_dotenv
import os
import threading

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
        self.channel.exchange_declare(exchange=exchange, exchange_type='direct')
        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)

    def send_message(self, message, routing_key):
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=json.dumps({'message': message, 'sent_to': routing_key}),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        self.log_message(message, sent_to=routing_key)

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
            routing_key='',
            body=json.dumps(log_entry),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )

    def process_message(self, message):
        raise NotImplementedError

    def callback(self, ch, method, properties, body):
        message = json.loads(body)
        self.log_message(f"Received: {message}", received_from=self.name)
        self.process_message(message)

    def start_receiving(self):
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=True)
        print(f"[{self.name}] Waiting for messages...")
        threading.Thread(target=self.channel.start_consuming).start()

    
