import json
import time
import os
import pika
import ssl
from dotenv import load_dotenv


prefix = "s3_"
# Load environment variables from .env file
load_dotenv()

def load_scenarios(file_path):
    with open(file_path, 'r') as file:
        scenarios = json.load(file)
    return scenarios

def get_rabbitmq_connection():
    rabbitmq_user = os.getenv('RABBITMQ_USER')
    rabbitmq_pass = os.getenv('RABBITMQ_PASS')
    rabbitmq_host = os.getenv('RABBITMQ_HOST')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT'))

    if not all([rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_port]):
        raise ValueError("RabbitMQ configuration is missing in the environment variables.")

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    
    # SSL context setup with disabled verification
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=600,
        ssl_options=pika.SSLOptions(context)
    )
    
    connection = pika.BlockingConnection(parameters)
    return connection

def publish_message(channel, message, routing_key):
    channel.basic_publish(
        exchange='amq.topic',
        routing_key=routing_key,
        body=json.dumps(message)
    )
    print(f"Sent data to Assembly Agent with routing key {routing_key}")

def simulate_scenario(channel, data):
    message = data
    publish_message(channel, message, f"{prefix}ai_assembly")

def main():
    scenarios = load_scenarios('scenarios.json')
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    try:
        while True:
            for details in scenarios:
                print(f"Simulating scenario with details: {details}")
                simulate_scenario(channel, details)
                time.sleep(10)
    finally:
        connection.close()

if __name__ == "__main__":
    main()
