# Python Script with YAML Integration

import glob
from pdb import run
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
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def forward_message(channel, forward_queue, forward_route, message):
    """Forward a message to the specified queue."""
    channel.basic_publish(
        exchange='amq.topic',
        routing_key=forward_route,
        body=json.dumps(message)
    )
    logger.info(f"Message forwarded to {forward_queue} via route {forward_route}.")

# Tools
tools = [capgeminiDocumentsTool(), actionTool(), Agent2AgentTool(), CallTool()]

def setup_prompt(userinfo, agentlocation, userlocation, config):
    """Set up the prompt template."""
    logger.info("Setting up prompt")
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                config['prompts']['system'].format(userinfo=userinfo, agentlocation=agentlocation, userlocation=userlocation)
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )


def process_ai_response(response):
    """Process the AI response to extract actions."""
    try:
        # Check if response is a string
        if isinstance(response, str):
            logger.info(f"Raw AI Response: {response}")

            # Pattern to match actions and their content
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
        message = json.loads(body)
        userquestion = message.get('userquestion', 'No question provided')
        userinfo = message.get('user_id', 'Unknown user')
        userlocation = message.get('user_location', 'Unknown location')
        agentlocation = message.get('agent_location', 'Unknown location')
        session_id = userinfo

        logger.info(f"User Info: {userinfo}")
        logger.info(f"User Location: {userlocation}")
        logger.info(f"Agent Location: {agentlocation}")
        logger.info(f"User Question: {userquestion}")

        prompt = setup_prompt(userinfo, agentlocation, userlocation, config)
        
        #convert to string
        prompt = str(prompt)
        
        logger.info(f"Prompt: {prompt}")
        
        ############################################
        # AUTOGEN CODE
        response = run_agent("ai_master", userquestion, prompt)


        logger.info(f"Raw AI response: {response}")
        formatted_response = process_ai_response(response)

        # Publish the response to the publish queue
        logger.info(f"Publishing to {config['queues']['publish']} with routing key {config['queues']['publish_route']}")
        channel.basic_publish(
            exchange='amq.topic',
            routing_key=config['queues']['publish_route'],
            body=json.dumps(formatted_response)
        )
        logger.info(f"Published response to {config['queues']['publish']} via route {config['queues']['publish_route']}")

        # Forward the message if necessary
        # if config['agent_name'] == 'assembly' and actions(userlocation, userquestion, response):
        #     forward_message(channel, config['queues']['forward'], config['queues']['forward_route'], message)
        # elif config['agent_name'] == 'quality' and actions(userlocation, userquestion, response):
        #     forward_message(channel, config['queues']['forward'], config['queues']['forward_route'], message)
        # elif config['agent_name'] == 'master':
        #     logger.info("Master agent does not forward messages")

    except json.JSONDecodeError:
        logger.error("Received message is not in JSON format. Here is the raw message:")
        logger.error(body.decode('utf-8'))
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
            
###################################

            rabbitmq_user = os.getenv('RABBITMQ_USER')
            rabbitmq_pass = os.getenv('RABBITMQ_PASS')
            rabbitmq_host = os.getenv('RABBITMQ_HOST')
            rabbitmq_port = int(os.getenv('RABBITMQ_PORT'))

            if not all([rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_port]):
                logger.error("RabbitMQ configuration is missing in the environment variables.")
                sys.exit(1)

            # SSL context setup with disabled verification
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE        

            credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
            parameters = pika.ConnectionParameters(
                host=rabbitmq_host, 
                port=rabbitmq_port, 
                credentials=credentials,
                heartbeat=60,  
                blocked_connection_timeout=600 ,
                ssl_options=pika.SSLOptions(context)
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
###################################
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
