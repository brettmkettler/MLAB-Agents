import glob
import sys
import yaml
import json
import re
import time
import os
import logging
import ssl

import pika
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Type

from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationBufferMemory

from agent_tools import capgeminiDocumentsTool, CallTool, actionTool, Agent2AgentTool, makeCall
from agent_llm import run_agent

# Load environment variables
load_dotenv()

# Global Channel
channel = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(agent_name):
    """Load the configuration file for the given agent."""
    config_file = f"{agent_name}Agent.yaml"
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            if not isinstance(config, dict):
                raise ValueError("The loaded config is not a dictionary.")
            return config
    except yaml.YAMLError as e:
        logger.error(f"Error loading YAML configuration: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"Configuration file {config_file} not found.")
        sys.exit(1)
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

def forward_message(channel, forward_queue, forward_route, message):
    """Forward a message to the specified queue."""
    try:
        channel.basic_publish(
            exchange='amq.topic',
            routing_key=forward_route,
            body=json.dumps(message)
        )
        logger.info(f"Message forwarded to {forward_queue} via route {forward_route}.")
    except Exception as e:
        logger.error(f"Failed to forward message: {e}")

# Tools
tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool(), CallTool()]

def setup_prompt(userinfo, agentlocation, userlocation, config):
    """Set up the prompt template."""
    logger.info("Setting up prompt")
    try:
        system_prompt = config['prompts']['system'].format(userinfo=userinfo, agentlocation=agentlocation, userlocation=userlocation)
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
    except KeyError as e:
        logger.error(f"Configuration missing key: {e}")
        sys.exit(1)

def process_ai_response(response):
    """Process the AI response to extract actions."""
    try:
        if isinstance(response, str):
            logger.info(f"Raw AI Response: {response}")

            action_pattern = r'"action": "(\w+)", "content": "([^"]*)"'
            actions = re.findall(action_pattern, response)

            if not actions:
                logger.warning("No valid actions found in the AI response.")
                return {"error": "No valid actions found in the AI response."}

            action_types = {"GOTO": "None", "POINTAT": "None", "TALK": "None", "USERID": "None"}

            for action_type, action_content in actions:
                if action_type in action_types:
                    action_types[action_type] = action_content

            actions_list = [
                {"action": "GOTO", "content": action_types["GOTO"]},
                {"action": "POINTAT", "content": action_types["POINTAT"]},
                {"action": "TALK", "content": action_types["TALK"]},
                {"action": "USERID", "content": action_types["USERID"]}
            ]

            formatted_response = {"response": actions_list}
            logger.info(f"Formatted Response: {formatted_response}")
            return formatted_response
        else:
            logger.warning("No valid response from the AI.")
            return {"error": "No valid response from the AI."}
    except Exception as e:
        logger.error(f"Error processing AI response: {e}")
        return {"error": str(e)}



def handle_message(channel, method, properties, body, config):
    """Handle incoming messages from the queue."""
    logger.info(f"Received raw message: {body}")
    
    try:
        message_dict = json.loads(body)
        print("Message Dict: ", message_dict)
    except json.JSONDecodeError:
        logger.error("Received message is not in JSON format. Here is the raw message:")
        logger.error(body.decode('utf-8'))
    finally:
        channel.basic_ack(delivery_tag=method.delivery_tag)
        
    

    required_fields = ["userquestion", "user_id", "user_location", "agent_location"]
    
    if all(key in message_dict for key in required_fields):
        print("All required fields are present")
        try:
            userquestion = message_dict['userquestion']
            userinfo = message_dict['user_id']
            userlocation = message_dict['user_location']
            agentlocation = message_dict['agent_location']
            session_id = userinfo

            logger.info(f"User Info: {userinfo}")
            logger.info(f"User Location: {userlocation}")
            logger.info(f"Agent Location: {agentlocation}")
            logger.info(f"User Question: {userquestion}")

            prompt = setup_prompt(userinfo, agentlocation, userlocation, config)
            
            prompt_str = str(prompt)
            
            logger.info(f"Prompt: {prompt_str}")
            
            response = run_agent(agent_name, userquestion, prompt_str)
            logger.info(f"Raw AI response: {response}")
            formatted_response = process_ai_response(response)

            logger.info(f"Publishing to {config['queues']['publish']} with routing key {config['queues']['publish_route']}")
            channel.basic_publish(
                exchange='amq.topic',
                routing_key=config['queues']['publish_route'],
                body=json.dumps(formatted_response)
            )
            logger.info(f"Published response to {config['queues']['publish']} via route {config['queues']['publish_route']}")

        except KeyError as e:
            logger.error(f"Missing key in message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
        finally:
            channel.basic_ack(delivery_tag=method.delivery_tag)
    else:
        try:
            logger.warning("Message does not have the required fields. This is a system message...")
            prompt = """
            You are a factory worker in a digital twin laboratory. You are responsible for monitoring the system logs and analyzing the data.

            This is a message from the system which is a log, you need to store this in your memory and analyze the data. 
            """
            
            #convert body to string
            body = body.decode('utf-8')
            
            response = run_agent(agent_name, body, prompt)
            
            logger.info(f"Raw AI response: {response}")
            
            print(response)
            # continue to the next message
        except KeyError as e:
            logger.error(f"Missing key in message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
        finally:
            channel.basic_ack(delivery_tag=method.delivery_tag)


        
        
        

def connect_and_consume(agent_name):
    """Connect to RabbitMQ and start consuming messages."""
    global channel
    while True:
        try:
            config = load_config(agent_name)
            
            rabbitmq_user = os.getenv('RABBITMQ_USER')
            rabbitmq_pass = os.getenv('RABBITMQ_PASS')
            rabbitmq_host = os.getenv('RABBITMQ_HOST')
            rabbitmq_port = int(os.getenv('RABBITMQ_PORT'))

            if not all([rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_port]):
                logger.error("RabbitMQ configuration is missing in the environment variables.")
                sys.exit(1)

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE        

            credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
            parameters = pika.ConnectionParameters(
                host=rabbitmq_host, 
                port=rabbitmq_port, 
                credentials=credentials,
                heartbeat=60,  
                blocked_connection_timeout=600,
                ssl_options=pika.SSLOptions(context)
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            channel.basic_consume(queue=config['queues']['listen'], on_message_callback=lambda ch, method, properties, body: handle_message(ch, method, properties, body, config))

            logger.info(f'Waiting for messages from "{config["queues"]["listen"]}". To exit press CTRL+C')
            channel.start_consuming()
        except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelError) as e:
            logger.error(f"Connection error: {e}. Reconnecting in 10 seconds...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Reconnecting in 10 seconds...")
            time.sleep(10)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.error("Usage: python AMQP_AI_Agent.py <agent_name>")
        sys.exit(1)
    agent_name = sys.argv[1]
    connect_and_consume(agent_name)
