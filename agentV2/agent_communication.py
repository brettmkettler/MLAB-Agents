import os
import json
import logging
import pika
import ssl
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Communication:
    def __init__(self, config):
        self.config = config
        self.channel = None
        self.connection = None
    
    def setup_connection(self):
        rabbitmq_user = os.getenv('RABBITMQ_USER')
        rabbitmq_pass = os.getenv('RABBITMQ_PASS')
        rabbitmq_host = os.getenv('RABBITMQ_HOST')
        rabbitmq_port = int(os.getenv('RABBITMQ_PORT'))
        
        if not all([rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_port]):
            logger.error("RabbitMQ configuration is missing in the environment variables.")
            sys.exit(1)
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host, 
            port=rabbitmq_port, 
            credentials=credentials,
            heartbeat=60,  
            blocked_connection_timeout=600,
            ssl_options=pika.SSLOptions(context)
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
    
    def send_message(self, message, route):
        self.channel.basic_publish(
            exchange='amq.topic',
            routing_key=route,
            body=json.dumps(message)
        )
        logger.info(f"Message sent to route {route}.")
        self.log_message(message, route)
    
    def log_message(self, message, route):
        log_entry = {
            "route": route,
            "message": message
        }
        self.channel.basic_publish(
            exchange='log_exchange',
            routing_key='',
            body=json.dumps(log_entry),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        # Persist to file or DB
        with open('communications.log', 'a') as log_file:
            log_file.write(json.dumps(log_entry) + "\n")
