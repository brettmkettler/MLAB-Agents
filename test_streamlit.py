import streamlit as st
import pika
import json
import threading
import time
import os
from dotenv import load_dotenv
import logging
import ssl

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load RabbitMQ credentials from environment variables
rabbitmq_user = os.getenv('RABBITMQ_USER')
rabbitmq_pass = os.getenv('RABBITMQ_PASS')
rabbitmq_host = os.getenv('RABBITMQ_HOST')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT'))

# Define the queue names
listen_queue = 'unity_master_queue'
publish_queue = 'ai_master_queue'

# Global variable to store the response
response_message = None

def callback(ch, method, properties, body):
    """Callback function to handle incoming messages."""
    global response_message
    try:
        message = json.loads(body)
        response_message = message
        logger.info(f"Received message from {publish_queue}: {json.dumps(message, indent=2)}")
    except json.JSONDecodeError:
        logger.error(f"Received non-JSON message from {publish_queue}: {body}")
        response_message = {"ERROR": {"message": "Received non-JSON message"}}
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def listen_for_response():
    """Continuously listen for messages from RabbitMQ."""
    if not all([rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_port]):
        logger.error("RabbitMQ configuration is missing in the environment variables.")
        return

    # Setting up SSL context
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host, 
        port=rabbitmq_port, 
        credentials=credentials,
        ssl_options=pika.SSLOptions(context)
    )

    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.basic_consume(queue=publish_queue, on_message_callback=callback)
            logger.info("Listening for messages. To exit press CTRL+C")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error: {e}")
        except pika.exceptions.IncompatibleProtocolError as e:
            logger.error(f"Incompatible protocol error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        finally:
            logger.info("Reconnecting in 5 seconds...")
            time.sleep(5)

def start_listening_thread():
    """Start the listening thread."""
    listening_thread = threading.Thread(target=listen_for_response, daemon=True)
    listening_thread.start()

def send_message_to_queue(userquestion, user_id, user_location, agent_location):
    """Send a message to the RabbitMQ queue."""
    # Setting up SSL context
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host, 
        port=rabbitmq_port, 
        credentials=credentials,
        ssl_options=pika.SSLOptions(context)
    )
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        message = {
            'userquestion': userquestion,
            'user_id': user_id,
            'user_location': user_location,
            'agent_location': agent_location
        }
        channel.basic_publish(exchange='amq.topic', routing_key=listen_queue, body=json.dumps(message))
        connection.close()
    except pika.exceptions.AMQPConnectionError as e:
        st.error(f"Connection error: {e}")
    except pika.exceptions.IncompatibleProtocolError as e:
        st.error(f"Incompatible protocol error: {e}")
    except Exception as e:
        st.error(f"Failed to send message to queue: {e}")

def chat_with_bot(userquestion, user_id, user_location, agent_location):
    """Send a message to the queue and wait for a response."""
    global response_message
    response_message = None

    send_message_to_queue(userquestion, user_id, user_location, agent_location)

    timeout = time.time() + 10  # 10 seconds timeout
    while response_message is None and time.time() < timeout:
        time.sleep(1)

    return response_message

def display_response(response):
    """Display the response from the agent."""
    if response is None:
        st.write("No response received from the agent.")
        return

    if "ERROR" in response:
        st.write(f"Error: {response['ERROR']['message']}")
        return

    for action in response.get('response', []):
        if action['action'] == 'GOTO' and action['content'] != 'None':
            st.write("🚶")
            st.write(f"Location: {action['content']}")
        elif action['action'] == 'POINTAT' and action['content'] != 'None':
            st.write("👉")
            st.write(f"Pointing at: {action['content']}")
        elif action['action'] == 'TALK' and action['content'] != 'None':
            st.write(f"Gemi: {action['content']}")

def main():
    """Main function to interact with the user and display responses."""
    st.title("Chat with Gemi")

    user_id = st.text_input("User ID", "Brett Kettler")

    regions = [
        'REGION_VR', 'REGION_DIGITALPOKAYOKE', 'REGION_COBOT', 
        'REGION_TESTBENCH', 'REGION_UR3', 'REGION_SPEECH'
    ]

    user_location = st.selectbox("Select User's Region", regions)
    agent_location = st.selectbox("Select Agent's Region", regions)

    user_input = st.text_input("You:", "")

    if st.button("Send") and user_input:
        response = chat_with_bot(user_input, user_id, user_location, agent_location)

        if response:
            display_response(response)
        else:
            st.write("No response received. Please try again.")

        with st.expander("Show raw response data"):
            st.json(response)

if __name__ == '__main__':
    start_listening_thread()
    main()
