import pika
import time
import logging
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
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'AMQP_pipeline.log')
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

def connect_to_rabbitmq(host, port, username, password):
    try:
        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(host, port, '/', credentials)
        connection = pika.BlockingConnection(parameters)
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"Connection error: {e}")
        return None

def get_last_message_from_queue_a(channel):
    last_message = None
    message_count = 0
    try:
        method_frame, header_frame, body = channel.basic_get(queue=RABBITMQ_A_QUEUE, auto_ack=True)
        while method_frame:
            last_message = body
            message_count += 1
            method_frame, header_frame, body = channel.basic_get(queue=RABBITMQ_A_QUEUE, auto_ack=True)
    except pika.exceptions.AMQPError as e:
        logging.error(f"Error reading from queue A: {e}")
    return last_message, message_count

def publish_message_to_queue_b(channel, message):
    try:
        if message:
            channel.basic_publish(exchange='', routing_key=RABBITMQ_B_QUEUE, body=message)
    except pika.exceptions.AMQPError as e:
        logging.error(f"Error publishing to queue B: {e}")

def log_received_message(message):
    if message:
        with open('pure_messages.log', 'a') as file:
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}:\n{message.decode('utf-8')}\n\n")

def main():
    while True:
        connection_a = None
        connection_b = None
        try:
            # Connect to RabbitMQ A
            connection_a = connect_to_rabbitmq(RABBITMQ_A_HOST, RABBITMQ_A_PORT, RABBITMQ_A_USERNAME, RABBITMQ_A_PASSWORD)
            if not connection_a:
                logging.error("Failed to connect to RabbitMQ A. Retrying in a few seconds...")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            # Connect to RabbitMQ B
            connection_b = connect_to_rabbitmq(RABBITMQ_B_HOST, RABBITMQ_B_PORT, RABBITMQ_B_USERNAME, RABBITMQ_B_PASSWORD)
            if not connection_b:
                logging.error("Failed to connect to RabbitMQ B. Retrying in a few seconds...")
                connection_a.close()
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            # Both connections successful
            screen_logger.info(f"Connected {time.strftime('%d/%m/%Y %H:%M:%S')}")
            logging.info(f"Connected to RabbitMQ A and B at {time.strftime('%d/%m/%Y %H:%M:%S')}")

            channel_a = connection_a.channel()
            channel_a.queue_declare(queue=RABBITMQ_A_QUEUE, durable=True)

            channel_b = connection_b.channel()
            channel_b.queue_declare(queue=RABBITMQ_B_QUEUE, durable=True)

            # Get the last message from Queue A
            last_message, message_count = get_last_message_from_queue_a(channel_a)
            if message_count == 0:
                screen_logger.info("Received 0 messages")
            else:
                log_received_message(last_message)
                logging.info(f"Received message: {last_message.decode('utf-8')}")
                publish_message_to_queue_b(channel_b, last_message)
                screen_logger.info(f"Received {message_count} messages, sent 1 message")
                screen_logger.info(f"Msg : {last_message.decode('utf-8')[:50]}")

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
        
        finally:
            if connection_a:
                connection_a.close()
            if connection_b:
                connection_b.close()

        # Wait for the specified interval before polling again
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
