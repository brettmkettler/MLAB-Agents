# Shows all log in a simple singl page application
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
app.config['SECRET_KEY'] = 'secretAsh2!'
socketio = SocketIO(app)

def rabbitmq_listener():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST'),
            port=int(os.getenv('RABBITMQ_PORT')),
            credentials=pika.PlainCredentials(os.getenv('AI_USER'), os.getenv('AI_PASS'))
        )
    )
    channel = connection.channel()
    channel.exchange_declare(exchange='log_exchange', exchange_type='fanout')
    channel.queue_declare(queue='log_queue', durable=True)
    channel.queue_bind(exchange='log_exchange', queue='log_queue')

    def callback(ch, method, properties, body):
        log_message = json.loads(body)
        socketio.emit('log_message', log_message)

    channel.basic_consume(queue='log_queue', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

@app.route('/')
def index():
    return render_template('index_s.html')

if __name__ == '__main__':
    threading.Thread(target=rabbitmq_listener).start()
    socketio.run(app, host='0.0.0.0', port=5001)
