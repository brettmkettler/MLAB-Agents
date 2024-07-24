import pika
from dotenv import load_dotenv
import os
import ssl


# Load environment variables from .env file
load_dotenv()

def delete_agent_exchange_and_queues(channel, connection):
    queues = [
        ('unity_assembly', 'unity_assembly_queue'),
        ('ai_assembly', 'ai_assembly_queue'),
        ('unity_quality', 'unity_quality_queue'),
        ('ai_quality', 'ai_quality_queue'),
        ('unity_master', 'unity_master_queue'),
        ('ai_master', 'ai_master_queue'),
        ('call_ms_teams', 'call_ms_teams_queue'),
        ('DigitalPokaYoke_bot', 'DigitalPokaYoke_bot_queue'),
        ('log', 'log_queue')  # Add log_queue to the deletion list
    ]

    for routing_key, queue_name in queues:
        try:
            channel.queue_delete(queue=queue_name)
            print(f"Queue {queue_name} deleted.")
        except pika.exceptions.ChannelClosedByBroker:
            print(f"Queue {queue_name} does not exist.")
            channel = connection.channel()  # Re-open the channel if it was closed

    try:
        channel.exchange_delete(exchange='agent_exchange')
        print("Exchange 'agent_exchange' deleted.")
    except pika.exceptions.ChannelClosedByBroker:
        print("Exchange 'agent_exchange' does not exist.")
        channel = connection.channel()  # Re-open the channel if it was closed

def create_agent_exchange_and_queues(channel):
    # Create exchanges
    channel.exchange_declare(exchange='agent_exchange', exchange_type='direct')
    print("Exchange 'agent_exchange' created.")
    channel.exchange_declare(exchange='log_exchange', exchange_type='fanout')
    print("Exchange 'log_exchange' created.")

    # Create routing/queues and bind them to the agent exchange
    queues = [
        ('unity_assembly', 'unity_assembly_queue'),
        ('ai_assembly', 'ai_assembly_queue'),
        ('unity_quality', 'unity_quality_queue'),
        ('ai_quality', 'ai_quality_queue'),
        ('unity_master', 'unity_master_queue'),
        ('ai_master', 'ai_master_queue'),
        ('call_ms_teams', 'call_ms_teams_queue'),
        ('DigitalPokaYoke_bot', 'DigitalPokaYoke_bot_queue')
    ]

    for routing_key, queue_name in queues:
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(exchange='agent_exchange', queue=queue_name, routing_key=routing_key)
        print(f"Queue {queue_name} created and bound to 'agent_exchange' with routing key '{routing_key}'.")

    # Create log queue with TTL and bind it to the log exchange
    args = {
        'x-message-ttl': 86400000  # 24 hours in milliseconds
    }
    channel.queue_declare(queue='log_queue', durable=True, arguments=args)
    channel.queue_bind(exchange='log_exchange', queue='log_queue')
    print("Queue 'log_queue' created with TTL and bound to 'log_exchange'.")

    # Bind queues to the existing exchange 'amq.topic'
    existing_exchange = 'amq.topic'
    bindings = [
        ('unity_assembly', 'unity_assembly_queue'),
        ('ai_assembly', 'ai_assembly_queue'),
        ('unity_quality', 'unity_quality_queue'),
        ('ai_quality', 'ai_quality_queue'),
        ('unity_master', 'unity_master_queue'),
        ('ai_master', 'ai_master_queue')
    ]

    for routing_key, queue_name in bindings:
        channel.queue_bind(exchange=existing_exchange, queue=queue_name, routing_key=routing_key)
        print(f"Queue {queue_name} bound to '{existing_exchange}' with routing key '{routing_key}'.")

def setup_rabbitmq(delete_existing=True):
    print(f"Setting up RabbitMQ...")
    print(f"RabbitMQ host: {os.getenv('RABBITMQ_HOST')} , port: {os.getenv('RABBITMQ_PORT')}")

    # SSL context setup with disabled verification
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=os.getenv('RABBITMQ_HOST'),
        port=int(os.getenv('RABBITMQ_PORT')),
        credentials=pika.PlainCredentials(os.getenv('AI_USER'), os.getenv('AI_PASS')),
        blocked_connection_timeout=600,
        ssl_options=pika.SSLOptions(context)
    ))
    channel = connection.channel()

    if delete_existing:
        delete_agent_exchange_and_queues(channel, connection)

    create_agent_exchange_and_queues(channel)

    connection.close()

setup_rabbitmq(delete_existing=True)  # Set to False if you want to disable deletion
