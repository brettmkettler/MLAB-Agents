import pika
from dotenv import load_dotenv
import os
import ssl

# Load environment variables from .env file
load_dotenv('./.env')

# Define the prefix variable
prefix = "v2_"

def delete_agent_exchange_and_queues(channel, connection):
    queues = [
        (f'{prefix}unity_assembly', f'{prefix}unity_assembly_queue'),
        (f'{prefix}ai_assembly', f'{prefix}ai_assembly_queue'),
        (f'{prefix}unity_quality', f'{prefix}unity_quality_queue'),
        (f'{prefix}ai_quality', f'{prefix}ai_quality_queue'),
        (f'{prefix}unity_master', f'{prefix}unity_master_queue'),
        (f'{prefix}ai_master', f'{prefix}ai_master_queue'),
        (f'{prefix}log', f'{prefix}log_queue')  # Add log_queue to the deletion list
    ]

    for routing_key, queue_name in queues:
        try:
            channel.queue_delete(queue=queue_name)
            print(f"Queue {queue_name} deleted.")
        except pika.exceptions.ChannelClosedByBroker:
            print(f"Queue {queue_name} does not exist.")
            channel = connection.channel()  # Re-open the channel if it was closed

    try:
        channel.exchange_delete(exchange=f'{prefix}agent_exchange')
        print(f"Exchange '{prefix}agent_exchange' deleted.")
    except pika.exceptions.ChannelClosedByBroker:
        print(f"Exchange '{prefix}agent_exchange' does not exist.")
        channel = connection.channel()  # Re-open the channel if it was closed

def create_agent_exchange_and_queues(channel):
    # Create exchanges
    channel.exchange_declare(exchange=f'{prefix}agent_exchange', exchange_type='direct')
    print(f"Exchange '{prefix}agent_exchange' created.")
    channel.exchange_declare(exchange=f'{prefix}log_exchange', exchange_type='fanout')
    print(f"Exchange '{prefix}log_exchange' created.")

    # Create routing/queues and bind them to the agent exchange
    queues = [
        (f'{prefix}unity_assembly', f'{prefix}unity_assembly_queue'),
        (f'{prefix}ai_assembly', f'{prefix}ai_assembly_queue'),
        (f'{prefix}unity_quality', f'{prefix}unity_quality_queue'),
        (f'{prefix}ai_quality', f'{prefix}ai_quality_queue'),
        (f'{prefix}unity_master', f'{prefix}unity_master_queue'),
        (f'{prefix}ai_master', f'{prefix}ai_master_queue')
    ]

    for routing_key, queue_name in queues:
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(exchange=f'{prefix}agent_exchange', queue=queue_name, routing_key=routing_key)
        print(f"Queue {queue_name} created and bound to '{prefix}agent_exchange' with routing key '{routing_key}'.")

    # Create log queue with TTL and bind it to the log exchange
    args = {
        'x-message-ttl': 86400000  # 24 hours in milliseconds
    }
    channel.queue_declare(queue=f'{prefix}log_queue', durable=True, arguments=args)
    channel.queue_bind(exchange=f'{prefix}log_exchange', queue=f'{prefix}log_queue')
    print(f"Queue '{prefix}log_queue' created with TTL and bound to '{prefix}log_exchange'.")

    # Bind queues to the existing exchange 'amq.topic'
    existing_exchange = 'amq.topic'
    bindings = [
        (f'{prefix}unity_assembly', f'{prefix}unity_assembly_queue'),
        (f'{prefix}ai_assembly', f'{prefix}ai_assembly_queue'),
        (f'{prefix}unity_quality', f'{prefix}unity_quality_queue'),
        (f'{prefix}ai_quality', f'{prefix}ai_quality_queue'),
        (f'{prefix}unity_master', f'{prefix}unity_master_queue'),
        (f'{prefix}ai_master', f'{prefix}ai_master_queue')
    ]

    for routing_key, queue_name in bindings:
        channel.queue_bind(exchange=existing_exchange, queue=queue_name, routing_key=routing_key)
        print(f"Queue {queue_name} bound to '{existing_exchange}' with routing key '{routing_key}'.")

def setup_rabbitmq(delete_existing=True):
    rabbitmq_user = os.getenv(f'ai_USER')
    rabbitmq_pass = os.getenv(f'ai_PASS')
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    if not rabbitmq_user or not rabbitmq_pass:
        raise ValueError("RabbitMQ user or password environment variables are not set")

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=os.getenv('RABBITMQ_HOST'),
        port=int(os.getenv('RABBITMQ_PORT')),
        credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_pass),
        ssl_options=pika.SSLOptions(context)
    ))
    channel = connection.channel()

    if delete_existing:
        delete_agent_exchange_and_queues(channel, connection)

    create_agent_exchange_and_queues(channel)

    connection.close()

setup_rabbitmq(delete_existing=True)  # Set to False if you want to disable deletion
