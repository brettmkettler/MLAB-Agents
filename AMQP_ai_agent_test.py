import pika
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
AI_USER = os.getenv('AI_USER')
AI_PASS = os.getenv('AI_PASS')

# Sample message
message = {
    "userquestion": "Hi, how is the factory doing today?",
    "user_id": "Ash",
    "user_location": "Lab-1",
    "agent_location": "AshHome"
}

def send_message(channel):
    # Publish the message
    channel.basic_publish(
        exchange='AIFactory',
        routing_key='ai_assessment',
        body=json.dumps(message)
    )
    print("Message sent to the route 'ai_assessment'.")

def callback(ch, method, properties, body):
    print("Received raw message:", body)
    try:
        response = json.loads(body)
        print("Received response from 'unity_assessment':", response)
    except json.JSONDecodeError:
        print("Received message is not in JSON format. Here is the raw message:")
        print(body.decode('utf-8'))  # Decode and print the raw message as text
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # Close the connection after receiving the response
        ch.connection.close()

def main():
    # Set up RabbitMQ connection and channel
    credentials = pika.PlainCredentials(AI_USER, AI_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Send the message
    send_message(channel)

    # Set up the consumer for the unity_assessment queue
    channel.basic_consume(queue='unity_assessment_queue', on_message_callback=callback)

    print('Waiting for response from "unity_assessment_queue". To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    main()
