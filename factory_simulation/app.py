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
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def rabbitmq_log_listener():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST'),
            port=int(os.getenv('RABBITMQ_PORT')),
            credentials=pika.PlainCredentials(os.getenv('AI_USER'), os.getenv('AI_PASS'))
        )
    )
    channel = connection.channel()
    channel.exchange_declare(exchange='log_exchange', exchange_type='fanout')
    args = {
        'x-message-ttl': 86400000  # 24 hours in milliseconds
    }
    channel.queue_declare(queue='log_queue', durable=True, arguments=args)
    channel.queue_bind(exchange='log_exchange', queue='log_queue')

    def callback(ch, method, properties, body):
        log_message = json.loads(body)
        print(f"[LogObserver] {log_message}")
        if 'sent_to' in log_message:
            queue_name = log_message['sent_to']
            print(f"[LogObserver] Sent to {log_message['sent_to']}")
        elif 'received_from' in log_message:
            queue_name = log_message['received_from']
            print(f"[LogObserver] Received from {log_message['received_from']}")
        else:
            queue_name = 'unknown'
            print(f"[LogObserver] Q unknown")
        
        socketio.emit('log_message', {'queue': queue_name, 'message': log_message['message'] })

    channel.basic_consume(queue='log_queue', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=rabbitmq_log_listener).start()
    socketio.run(app, host='0.0.0.0', port=5002)
