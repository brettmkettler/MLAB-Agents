import pika
import json
import os
from dotenv import load_dotenv
import ssl

# Load environment variables
load_dotenv()

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
AI_USER = os.getenv('AI_USER')
AI_PASS = os.getenv('AI_PASS')

# Sample message
message = {
    "userquestion": "What are the URLs?",
    "user_id": "Brett Kettler",
    "user_location": "Lab",
    "agent_location": "Lab"
}

def send_message(channel):
    # Publish the message
    channel.basic_publish(
        exchange='amq.topic',
        routing_key='s3_ai_assembly',
        body=json.dumps(message)
    )
    print("Message sent to the route 's3_ai_assembly'.")

def callback(ch, method, properties, body):
    print("Received raw message:", body)
    try:
        response = json.loads(body)
        print("Received response from 's3_unity_assembly':", response)
    except json.JSONDecodeError:
        print("Received message is not in JSON format. Here is the raw message:")
        print(body.decode('utf-8'))  # Decode and print the raw message as text
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # Close the connection after receiving the response
        ch.connection.close()

def main():
    # Set up RabbitMQ connection and channel
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  
    credentials = pika.PlainCredentials(AI_USER, AI_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials, ssl_options=pika.SSLOptions(context))
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Send the message
    send_message(channel)

    # Set up the consumer for the unity_assembly queue
    # channel.basic_consume(queue='unity_assembly_queue', on_message_callback=callback)

    # print('Waiting for response from "unity_assembly_queue". To exit press CTRL+C')
    # channel.start_consuming()

if __name__ == '__main__':
    main()
