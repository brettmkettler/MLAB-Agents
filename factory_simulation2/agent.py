import pika
import json
import os
import threading
from dotenv import load_dotenv
from autogen import Agent as AutoGenAgent, Message

# Load environment variables from .env file
load_dotenv()

class Agent:
    def __init__(self, name, exchange, routing_key, queue, user, password):
        self.name = name
        self.exchange = exchange
        self.routing_key = routing_key
        self.queue = queue
        self.auto_gen_agent = AutoGenAgent(name=name)

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST'),
                port=int(os.getenv('RABBITMQ_PORT')),
                credentials=pika.PlainCredentials(user, password)
            )
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=exchange, exchange_type='direct')
        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)

        # Register function handlers for inter-agent communication
        self.auto_gen_agent.register_function(self.send_to_assessment, name='send_to_assessment')
        self.auto_gen_agent.register_function(self.send_to_quality, name='send_to_quality')
        self.auto_gen_agent.register_function(self.send_to_master, name='send_to_master')
        self.auto_gen_agent.register_function(self.send_msg, name='send_msg')

    def send_message(self, message, routing_key):
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        self.log_message(message, sent_to=routing_key)

    def log_message(self, message, sent_to=None, received_from=None):
        log_entry = {'message': message}
        if sent_to:
            log_entry['sent_to'] = sent_to
            print(f"[{self.name}] sent to '{sent_to}': {message}")
        if received_from:
            log_entry['received_from'] = received_from
            print(f"[{self.name}] received from '{received_from}': {message}")

        self.channel.basic_publish(
            exchange='log_exchange',
            routing_key='',
            body=json.dumps(log_entry),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )

    def process_message(self, message):
        print(f"[{self.name}] Processing message: {message}")
        inner_msg = json.loads(message)

        # Load the prompt from a file
        with open(f'{self.name}.prompt.md', 'r') as file:
            prompt_template = file.read()

        prompt = prompt_template.format(data=json.dumps(inner_msg, indent=2))
        
        # Call the LLM through AutoGen
        response = self.auto_gen_agent.send_message(Message(prompt=prompt, return_type='json'))
        llm_result = response.get('result', {})

        # If the LLM result contains a command to send a message to another agent or Unity
        if 'send_to_assessment' in llm_result:
            self.send_to_assessment(llm_result['send_to_assessment'])
        if 'send_to_quality' in llm_result:
            self.send_to_quality(llm_result['send_to_quality'])
        if 'send_to_master' in llm_result:
            self.send_to_master(llm_result['send_to_master'])

    def send_to_assessment(self, message):
        self.send_message(message, "unity_assessment")

    def send_to_quality(self, message):
        self.send_message(message, "unity_quality")

    def send_to_master(self, message):
        self.send_message(message, "unity_master")

    def send_msg(self, agent_name, message):
        if agent_name == "AssessmentAgent":
            self.send_to_assessment(message)
        elif agent_name == "QualityAgent":
            self.send_to_quality(message)
        elif agent_name == "MasterAgent":
            self.send_to_master(message)

    def callback(self, ch, method, properties, body):
        message = body.decode()
        self.log_message(f"Received: {message}", received_from=self.name)
        self.process_message(message)

    def start_receiving(self):
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=True)
        print(f"[{self.name}] Waiting for messages...")
        threading.Thread(target=self.channel.start_consuming).start()

# Example usage
if __name__ == "__main__":
    agent = Agent(
        name="AssemblyAgent",
        exchange="agent_exchange",
        routing_key="assembly",
        queue="assembly_queue",
        user=os.getenv("AI_USER"),
        password=os.getenv("AI_PASS")
    )
    agent.start_receiving()
