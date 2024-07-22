# Description: This file contains the code for the web application that will display the logs from the RabbitMQ queues for each Queue. 
# The application uses Flask and Flask-SocketIO to create a simple single-page application that displays the logs in real-time. 
# The application listens to the RabbitMQ queues and emits the log messages to the client using SocketIO. 
# The application also uses the dotenv library to load environment variables from a .env file.
from flask import Flask, render_template
from flask_socketio import SocketIO
import pika
import json
import threading
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretAsh!'
socketio = SocketIO(app)

def rabbitmq_listener(queue_name):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST'),
            port=int(os.getenv('RABBITMQ_PORT')),
            credentials=pika.PlainCredentials(os.getenv('AI_USER'), os.getenv('AI_PASS'))
        )
    )
    channel = connection.channel()
    channel.exchange_declare(exchange='agent_exchange', exchange_type='direct')
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange='agent_exchange', queue=queue_name, routing_key=queue_name)

    def callback(ch, method, properties, body):
        log_message = json.loads(body)
        socketio.emit('log_message', {'queue': queue_name, 'message': log_message})

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

@app.route('/')
def index():
    return render_template('index_old.html')

if __name__ == '__main__':
    queues = ['ai_assembly_queue', 'ai_quality_queue', 'ai_master_queue', 'unity_assembly_queue', 'unity_quality_queue', 'unity_master_queue','call_ms_teams_queue','DigitalPokaYoke_bot_queue']
    for queue in queues:
        threading.Thread(target=rabbitmq_listener, args=(queue,)).start()
    socketio.run(app, host='0.0.0.0', port=5000)
