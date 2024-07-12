import pika
import json
from dotenv import load_dotenv
import os
import threading
import logging
import concurrent.futures
from agent_tools import CallTool, actionTool, capgeminiDocumentsTool, Agent2AgentTool, Agent2HumanTool
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Setup LLM
llm = ChatOpenAI(model="gpt-4")

tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool(), CallTool(), Agent2HumanTool()]

def setup_prompt(agent_name, userinfo, agentlocation, userlocation):
    logging.info("Setting up prompt")
    return ChatPromptTemplate.from_messages([
        ("system", f"""
            You are a helpful metaverse lab assistant named: {agent_name}. You are talking to {userinfo}.
            You are located here: {agentlocation}.
            The user is located here: {userlocation}.
            Use the searchDocuments tool to look up items about the lab. Use the Agent2Agent tool to ask other agents questions and respond back to agents that ask questions.
            If you receive a response from ai_master, ai_quality, or ai_assistant, forward the response to the user if needed.
        """),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

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
        
        
        
        ###########################################
        
        
        logging.info("Processing by LLM with data: %s", data)
        
        userquestion = data
        logging.info(f"Processing message from user: {userinfo}")

        session_id = userinfo
        
        prompt = setup_prompt(agent_name, userinfo, agentlocation, userlocation)
        
        agent = create_tool_calling_agent(llm, tools, prompt)
        
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        try:
            message_history = RedisChatMessageHistory(
                url=os.getenv("REDIS_URL"), ttl=100, session_id=session_id
            )
        except Exception as e:
            logging.error(f"Failed to initialize message history: {e}")
            message_history = None

        logging.info(f"Message history initialized for session: {session_id}")

        agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: message_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )

        logging.info("Invoking LLM with message history")
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(agent_with_chat_history.invoke, {"input": userquestion}, {"configurable": {"session_id": session_id}})
                response = future.result(timeout=30)  # Adjust timeout as necessary
        except concurrent.futures.TimeoutError:
            logging.error("Timeout while waiting for LLM response")
            response = {"output": "Timeout while processing the request."}
            
            
            
        ###########################################
        
        
        
        except Exception as e:
            logging.error(f"Error invoking LLM: {e}")
            response = {"output": "Error processing the request."}

        ai_response = response.get('output', "No valid response from the AI.")
        logging.info(f"AI Response: {ai_response}")

        return ai_response

    def process_message(self, message):
        try:
            inner_msg = message['message']
            userquestion = inner_msg.get('userquestion', None)
            userinfo = inner_msg.get('user_id', None)
            userlocation = inner_msg.get('user_location', None)
            agentlocation = inner_msg.get('agent_location', None)
            
            if userquestion:
                response = self.process_by_llm(self.name, inner_msg['userquestion'], userinfo, userlocation, agentlocation)
                self.send_message(response, routing_key=userinfo)
            else:
                response = self.process_by_llm(self.name, inner_msg, "Unknown User", "Unknown Location", "Unknown Location")
                # Here you could do something with the response if needed
        except KeyError as e:
            logging.error(f"[AIAssessmentAgent] KeyError: {e}. Message: {message}")
        except Exception as e:
            logging.error(f"[AIAssessmentAgent] Unexpected error: {e}. Message: {message}")

    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body)
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {e}. Body: {body}")
            return
        self.log_message(f"Received: {message}", received_from=self.name)
        self.process_message(message)

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
    import random
    from agent import Agent
    from dotenv import load_dotenv
    import os

    # Load environment variables
    load_dotenv()

    # Initialize the assessment agent
    assessment_agent = Agent(
        name="AIAssessmentAgent",
        exchange="agent_exchange",
        routing_key="ai_assessment",
        queue="ai_assessment_queue",
        user=os.getenv("AI_USER"),
        password=os.getenv("AI_PASS")
    )

    # Start receiving messages
    assessment_agent.start_receiving()

    # Blocking loop to keep the script running
    while True:
        pass
