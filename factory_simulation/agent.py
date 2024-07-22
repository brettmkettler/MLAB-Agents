import json
import os
import logging
import concurrent.futures
from dotenv import load_dotenv
import pika
from agent_tools import CallTool, actionTool, capgeminiDocumentsTool, Agent2AgentTool, Agent2HumanTool
from ai_agent_class import run_agent

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Define tools
#tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool(), CallTool(), Agent2HumanTool()]

class Agent:
    def __init__(self, name, exchange, routing_key, queue, user, password):
        self.name = name
        self.exchange = exchange
        self.routing_key = routing_key
        self.queue = queue
        self.user = user
        self.password = password
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.getenv('RABBITMQ_HOST'),
                    port=int(os.getenv('RABBITMQ_PORT')),
                    credentials=pika.PlainCredentials(self.user, self.password)
                )
            )
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct')
            self.channel.queue_declare(queue=self.queue, durable=True)
            self.channel.queue_bind(exchange=self.exchange, queue=self.queue, routing_key=self.routing_key)
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            self.reconnect()

    def reconnect(self):
        logging.info("Reconnecting to RabbitMQ...")
        self.close_connection()
        self.connect()
        
    def close_connection(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                logging.error(f"Error closing connection: {e}")

    def send_message(self, message, routing_key):
        try:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps({'message': message, 'sent_to': routing_key}),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            self.log_message(message, sent_to=routing_key)
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Connection error while sending message: {e}")
            self.reconnect()

    def log_message(self, message, sent_to=None, received_from=None):
        log_entry = {'message': message}
        if sent_to:
            log_entry['sent_to'] = sent_to
            logging.info(f"[{self.name}] sent to '{sent_to}' : {message}")
        if received_from:
            log_entry['received_from'] = received_from
            logging.info(f"[{self.name}] received from '{received_from}' : {message}")

        try:
            self.channel.basic_publish(
                exchange='log_exchange',
                routing_key='',
                body=json.dumps(log_entry),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Connection error while logging message: {e}")
            self.reconnect()

    def process_by_llm(self, agent_name, data, userinfo, userlocation, agentlocation):
        logging.info(f"Processing by LLM: {data}")
        userquestion = data
        session_id = userinfo
        
        ################################
        # Call LLM
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_agent, agent_name, userquestion, userinfo, userlocation, agentlocation)
                response = future.result(timeout=10)
                
                print(f"Response AutoGen: {response}")
                
        except concurrent.futures.TimeoutError:
            logging.error("Timeout while waiting for LLM response")
            response = {"output": "Timeout while processing the request."}
            
        ###########################################

        ai_response = response
        logging.info(f"AI Response: {ai_response}")

        return ai_response

    def process_message(self, message):
        try:
            inner_msg = message.get('message', {})
            if not isinstance(inner_msg, dict):
                inner_msg = json.loads(inner_msg)
            userquestion = inner_msg.get('userquestion', None)
            userinfo = inner_msg.get('user_id', None)
            userlocation = inner_msg.get('user_location', None)
            agentlocation = inner_msg.get('agent_location', None)
            
            if userquestion:
                response = self.process_by_llm(self.name, userquestion, userinfo, userlocation, agentlocation)
                self.send_message(response, routing_key=userinfo)
            else:
                response = self.process_by_llm(self.name, inner_msg, "Unknown User", "Unknown Location", "Unknown Location")
                # Here you could do something with the response if needed
        except KeyError as e:
            logging.error(f"[AIassemblyAgent] KeyError: {e}. Message: {message}")
        except Exception as e:
            logging.error(f"[AIassemblyAgent] Unexpected error: {e}. Message: {message}")

    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            self.log_message(f"Received: {message}", received_from=self.name)
            self.process_message(message)
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {e}. Body: {body}")
        except Exception as e:
            logging.error(f"Error processing message: {e}. Body: {body}")

    def start_receiving(self):
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=True)
        logging.info(f"[{self.name}] Waiting for messages...")
        while True:
            try:
                self.connection.process_data_events(time_limit=None)
            except pika.exceptions.AMQPConnectionError as e:
                logging.error(f"Connection error during message consumption: {e}")
                self.reconnect()

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    # Load environment variables
    load_dotenv()

    # Initialize the assembly agent
    assembly_agent = Agent(
        name="AIassemblyAgent",
        exchange="agent_exchange",
        routing_key="ai_assembly",
        queue="ai_assembly_queue",
        user=os.getenv("AI_USER"),
        password=os.getenv("AI_PASS")
    )

    # Start receiving messages
    assembly_agent.start_receiving()
