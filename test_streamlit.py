import streamlit as st
import pika
import json
import threading
import time
import os
from dotenv import load_dotenv
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

# Define the queue names
listen_queue = 'ai_master_queue'
publish_queue = 'unity_master_queue'

# Global variable to store the response
response_message = None

def callback(ch, method, properties, body, queue_name):
    global response_message
    try:
        message = json.loads(body)
        response_message = message
        logger.info(f"Received message from {queue_name}: {json.dumps(message, indent=2)}")
    except json.JSONDecodeError:
        logger.error(f"Received non-JSON message from {queue_name}: {body}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def listen_for_response():
    if not rabbitmq_user or not rabbitmq_pass or not rabbitmq_host or not rabbitmq_port:
        logger.error("RabbitMQ configuration is missing in the environment variables.")
        return

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.basic_consume(
        queue=publish_queue,
        on_message_callback=lambda ch, method, properties, body, queue_name=publish_queue: callback(ch, method, properties, body, queue_name)
    )

    logger.info("Listening for messages. To exit press CTRL+C")
    channel.start_consuming()

def start_listening_thread():
    listening_thread = threading.Thread(target=listen_for_response)
    listening_thread.daemon = True
    listening_thread.start()

def send_message_to_queue(userquestion, user_id, user_location, agent_location):
    try:
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        message = {
            'userquestion': userquestion,
            'user_id': user_id,
            'user_location': user_location,
            'agent_location': agent_location
        }
        
        channel.basic_publish(
            exchange='amq.topic',
            routing_key=listen_queue,
            body=json.dumps(message)
        )
        connection.close()
    except Exception as e:
        st.error(f"Failed to send message to queue: {e}")

def chat_with_bot(userquestion, user_id, user_location, agent_location):
    global response_message
    response_message = None
    
    send_message_to_queue(userquestion, user_id, user_location, agent_location)
    
    timeout = time.time() + 100  # 10 seconds timeout
    while response_message is None:
        if time.time() > timeout:
            print("Waiting")
        time.sleep(1)
    
    return response_message.get('response')

def display_response(response):
    for action in response:
        if action['action'] == 'GOTO' and action['content'] != 'None':
            st.write("🚶")
            st.write(f"Location: {action['content']}")
        elif action['action'] == 'POINTAT' and action['content'] != 'None':
            st.write("👉")
            st.write(f"Pointing at: {action['content']}")
        elif action['action'] == 'TALK':
            st.write(f"Gemi: {action['content']}")

def main():
    st.title("Chat with Gemi")

    user_id = st.text_input("User ID", "Brett Kettler")

    regions = [
        'REGION_VR', 'REGION_DIGITALPOKAYOKE', 'REGION_COBOT', 
        'REGION_TESTBENCH', 'REGION_UR3', 'REGION_SPEECH'
    ]
    
    user_location = st.selectbox("Select User's Region", regions)
    agent_location = st.selectbox("Select Agent's Region", regions)
    
    user_input = st.text_input("You:", "")

    if user_input:
        response = chat_with_bot(user_input, user_id, user_location, agent_location)
        
        print(response)
        
        if isinstance(response, list):
            display_response(response)
        else:
            st.write(response)
        
        with st.expander("Show raw response data"):
            st.json(response)

if __name__ == '__main__':
    start_listening_thread()
    main()
