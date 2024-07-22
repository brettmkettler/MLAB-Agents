import pika

# RabbitMQ Admin Credentials
admin_user = 'mlab'
admin_password = 'mlabAshBrett'
rabbitmq_host = '68.221.122.91'
c_exchange ='AIFactory'

# RabbitMQ AMQP settings for binding queues
rabbitmq_url = f'amqp://{admin_user}:{admin_password}@{rabbitmq_host}:5672/'

def setup_rabbitmq():
    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()

    # Declare exchange
    channel.exchange_declare(exchange=c_exchange, exchange_type='topic', durable=True)

    # Declare and bind queues
    queues = ['unityassemblyAgent', 'unityQualityAgent', 'unityMasterAgent']
    for queue in queues:
        channel.queue_declare(queue=queue, durable=True)
        channel.queue_bind(exchange=c_exchange, queue=queue, routing_key=queue)

    connection.close()

if __name__ == "__main__":
    setup_rabbitmq()
    print("RabbitMQ setup completed successfully.")
