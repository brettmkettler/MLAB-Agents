import pika
import time
import logging
import threading
from dotenv import load_dotenv
import os

load_dotenv()

# Load configurations from .env file
RABBITMQ_A_HOST = os.getenv('RABBITMQ_A_HOST')
RABBITMQ_A_PORT = int(os.getenv('RABBITMQ_A_PORT'))
RABBITMQ_A_USERNAME = os.getenv('RABBITMQ_A_USERNAME')
RABBITMQ_A_PASSWORD = os.getenv('RABBITMQ_A_PASSWORD')
RABBITMQ_A_QUEUE = os.getenv('RABBITMQ_A_QUEUE')

RABBITMQ_B_HOST = os.getenv('RABBITMQ_B_HOST')
RABBITMQ_B_PORT = int(os.getenv('RABBITMQ_B_PORT'))
RABBITMQ_B_USERNAME = os.getenv('RABBITMQ_B_USERNAME')
RABBITMQ_B_PASSWORD = os.getenv('RABBITMQ_B_PASSWORD')
RABBITMQ_B_QUEUE = os.getenv('RABBITMQ_B_QUEUE')

# Default poll interval in case of error
DEFAULT_POLL_INTERVAL_SECONDS = 10

# Load poll interval with error handling
try:
    POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', DEFAULT_POLL_INTERVAL_SECONDS))
except ValueError:
    POLL_INTERVAL_SECONDS = DEFAULT_POLL_INTERVAL_SECONDS

# Load log file path and log level from .env
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'AMQP_pipelineV2.log')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()

# Set up logging to file only
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.WARNING), format='%(asctime)s %(message)s', handlers=[
    logging.FileHandler(LOG_FILE_PATH)
])

# Create a custom logger for screen output only
screen_logger = logging.getLogger('screen')
screen_logger.setLevel(logging.INFO)
screen_handler = logging.StreamHandler()
screen_handler.setLevel(logging.INFO)
screen_formatter = logging.Formatter('%(message)s')
screen_handler.setFormatter(screen_formatter)
screen_logger.addHandler(screen_handler)

# Global variable for channel B and message buffer
channel_b = None
message_buffer = []
buffer_lock = threading.Lock()

def connect_to_rabbitmq(host, port, username, password):
    try:
        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(host, port, '/', credentials)
        connection = pika.BlockingConnection(parameters)
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"Connection error: {e}")
        return None

def on_message(channel, method_frame, header_frame, body):
    global message_buffer
    try:
        # Add message to the buffer
        with buffer_lock:
            message_buffer.append(body)

        # Manually acknowledge the message
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        # Optionally: send the message to a dead-letter queue (DLQ) or requeue
        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False)

def publish_message_to_queue_b(channel, message):
    try:
        if message:
            channel.basic_publish(exchange='', routing_key=RABBITMQ_B_QUEUE, body=message)
    except pika.exceptions.AMQPError as e:
        logging.error(f"Error publishing to queue B: {e}")

def log_received_message(message):
    if message:
        with open('pure_messagesV2.log', 'a') as file:
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}:\n{message.decode('utf-8')}\n\n")

def process_last_message():
    global message_buffer
    while True:
        time.sleep(POLL_INTERVAL_SECONDS)  # Wait for the specified time interval
        with buffer_lock:
            if message_buffer:
                last_message = message_buffer[-1]
                log_received_message(last_message)
                publish_message_to_queue_b(channel_b, last_message)
                screen_logger.info(f"Processed and sent last message: {last_message.decode('utf-8')[:50]}")
                message_buffer.clear()

def main():
    global channel_b

    connection_a = None
    connection_b = None
    channel_a = None

    try:
        # Connect to RabbitMQ A
        connection_a = connect_to_rabbitmq(RABBITMQ_A_HOST, RABBITMQ_A_PORT, RABBITMQ_A_USERNAME, RABBITMQ_A_PASSWORD)
        if not connection_a:
            logging.error("Failed to connect to RabbitMQ A.")
            screen_logger.info("Failed to connect to RabbitMQ A. Retrying...")
            time.sleep(POLL_INTERVAL_SECONDS)
            return

        # Connect to RabbitMQ B
        connection_b = connect_to_rabbitmq(RABBITMQ_B_HOST, RABBITMQ_B_PORT, RABBITMQ_B_USERNAME, RABBITMQ_B_PASSWORD)
        if not connection_b:
            logging.error("Failed to connect to RabbitMQ B.")
            screen_logger.info("Failed to connect to RabbitMQ B. Retrying...")
            time.sleep(POLL_INTERVAL_SECONDS)
            return

        # Log connection status
        screen_logger.info(f"Connected {time.strftime('%d/%m/%Y %H:%M:%S')}")
        logging.info(f"Connected to RabbitMQ A and B at {time.strftime('%d/%m/%Y %H:%M:%S')}")

        # Open channels
        channel_a = connection_a.channel()
        channel_b = connection_b.channel()

        # Declare queues
        channel_a.queue_declare(queue=RABBITMQ_A_QUEUE, durable=True)
        channel_b.queue_declare(queue=RABBITMQ_B_QUEUE, durable=True)

        # Set QoS for fair dispatch
        channel_a.basic_qos(prefetch_count=1)

        # Start a thread to process the last message every X seconds
        threading.Thread(target=process_last_message, daemon=True).start()

        # Start consuming messages with the callback function
        channel_a.basic_consume(queue=RABBITMQ_A_QUEUE, on_message_callback=on_message, auto_ack=False)

        # Start consuming
        screen_logger.info("Waiting for messages...")
        channel_a.start_consuming()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        screen_logger.info(f"An error occurred: {e}")

    finally:
        # Close connections gracefully
        if channel_a and channel_a.is_open:
            channel_a.close()
        if connection_a and connection_a.is_open:
            connection_a.close()
        if channel_b and channel_b.is_open:
            channel_b.close()
        if connection_b and connection_b.is_open:
            connection_b.close()

if __name__ == "__main__":
    main()
