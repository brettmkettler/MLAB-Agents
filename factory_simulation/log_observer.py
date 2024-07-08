import pika
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def callback(ch, method, properties, body):
    log_message = json.loads(body)
    if 'received_from' in log_message:
        print(f"[LogObserver] Received from {log_message['received_from']}: {log_message['message']}")
    elif 'sent_to' in log_message:
        print(f"[LogObserver] Sent to {log_message['sent_to']}: {log_message['message']}")
    else:
        print(f"[LogObserver] Log: {log_message}")
    with open('communication_log.txt', 'a') as log_file:
        log_file.write(json.dumps(log_message) + "\n")

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.getenv('RABBITMQ_HOST'),
        port=int(os.getenv('RABBITMQ_PORT')),
        credentials=pika.PlainCredentials(os.getenv('AI_USER'), os.getenv('AI_PASS'))
    )
)
channel = connection.channel()
# channel.exchange_declare(exchange='log_exchange', exchange_type='fanout')
# channel.queue_declare(queue='log_queue', durable=True)
# channel.queue_bind(exchange='log_exchange', queue='log_queue')

channel.basic_consume(queue='log_queue', on_message_callback=callback, auto_ack=True)
print("[LogObserver] Waiting for logs...")
channel.start_consuming()
