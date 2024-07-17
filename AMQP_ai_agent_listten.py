import pika
import os
from dotenv import load_dotenv
import json
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load RabbitMQ credentials from environment variables
rabbitmq_user = os.getenv('RABBITMQ_USER')
rabbitmq_pass = os.getenv('RABBITMQ_PASS')
rabbitmq_host = os.getenv('RABBITMQ_HOST')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT'))

def callback(ch, method, properties, body, queue_name):
    try:
        message = json.loads(body)
        logger.info(f"Received message from {queue_name}: {json.dumps(message, indent=2)}")
    except json.JSONDecodeError:
        logger.error(f"Received non-JSON message from {queue_name}: {body}")
    # Acknowledge the message to remove it from the queue
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    if not rabbitmq_user or not rabbitmq_pass or not rabbitmq_host or not rabbitmq_port:
        logger.error("RabbitMQ configuration is missing in the environment variables.")
        return

    # Set up RabbitMQ connection and channel
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    queues = ['unity_assessment_queue', 'unity_quality_queue', 'unity_master_queue']

    for queue in queues:
        channel.basic_consume(
            queue=queue,
            on_message_callback=lambda ch, method, properties, body, queue_name=queue: callback(ch, method, properties, body, queue_name)
        )

    logger.info("Listening for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    main()
