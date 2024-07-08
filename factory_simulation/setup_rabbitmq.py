import pika
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def delete_agent_exchange_and_queues(channel, connection):
    queues = [
        ('unity_assessment', 'unity_assessment_queue'),
        ('ai_assessment', 'ai_assessment_queue'),
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
        ('unity_assessment', 'unity_assessment_queue'),
        ('ai_assessment', 'ai_assessment_queue'),
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

def setup_rabbitmq(delete_existing=True):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=os.getenv('RABBITMQ_HOST'),
        port=int(os.getenv('RABBITMQ_PORT')),
        credentials=pika.PlainCredentials(os.getenv('AI_USER'), os.getenv('AI_PASS'))
    ))
    channel = connection.channel()

    if delete_existing:
        delete_agent_exchange_and_queues(channel, connection)

    create_agent_exchange_and_queues(channel)

    connection.close()

setup_rabbitmq(delete_existing=True)  # Set to False if you want to disable deletion
