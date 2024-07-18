import sys
import yaml
import pika
import json
import re
import time
from langchain.tools import BaseTool
from typing import Optional, Type
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationBufferMemory
import os
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(agent_name):
    config_file = f"{agent_name}Agent.yaml"
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def forward_message(channel, forward_queue, forward_route, message):
    channel.basic_publish(
        exchange='amq.topic',
        routing_key=forward_route,
        body=json.dumps(message)
    )
    logger.info(f"Message forwarded to {forward_queue} via route {forward_route}.")

def actions(userlocation, userquestion, response):
    logger.info("Deciding what actions to take...")
    logger.info(f"User's Location: {userlocation}")
    logger.info(f"User Question: {userquestion}")
    logger.info(f"Response: {response}")

    # Example: Assess if the log requires quality check
    if "quality issue" in userquestion.lower():
        return True
    return False

def searchDocuments(userquestion):
    logger.info("Searching for documents...")
    logger.info(f"User Question: {userquestion}")

    # Example: Mock documents and scores for demonstration
    docs_and_scores = [{"doc": "Mock document", "score": 0.9}]
    logger.info(f"Docs and Scores: {docs_and_scores}")
    return docs_and_scores

class capgeminiDocumentsInputs(BaseModel):
    question: str = Field(..., description="The entire question that the user asked.")

class capgeminiDocumentsTool(BaseTool):
    name = "searchDocuments"
    description = "Use this tool to search for information in the documents."

    def _run(self, question: str, *args, **kwargs):
        return searchDocuments(question)

    def _arun(self, question: str, *args, **kwargs):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = capgeminiDocumentsInputs

class actionInputs(BaseModel):
    userlocation: str = Field(..., description="The location of the user.")
    question: str = Field(..., description="The entire question that the user asked.")
    response: str = Field(..., description="The response from the agent.")

class actionTool(BaseTool):
    name = "actionTool"
    description = "Use this tool to decide what actions to take based on the user question and your response."

    def _run(self, userlocation:str, question: str, response: str, *args, **kwargs):
        return actions(userlocation, question, response)

    def _arun(self, question: str, response: str, *args, **kwargs):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = actionInputs

tools = [capgeminiDocumentsTool(), actionTool()]

def setupPrompt(userinfo, agentlocation, userlocation, config):
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
    try:
        if 'output' in response:
            ai_response = response['output']
            logger.info(f"AI Response: {ai_response}")
        else:
            logger.warning("No valid response from the AI.")
            return {"error": "No valid response from the AI."}

        action_pattern = r'"action": "(\w+)", "content": "([^"]*)"'
        actions = re.findall(action_pattern, ai_response)
        action_types = {"GOTO": "None", "POINTAT": "None", "TALK": "None"}

        for action_type, action_content in actions:
            action_types[action_type] = action_content

        actions_list = [
            {"action": "GOTO", "content": action_types["GOTO"]},
            {"action": "POINTAT", "content": action_types["POINTAT"]},
            {"action": "TALK", "content": action_types["TALK"]}
        ]

        formatted_response = {"response": actions_list}
        logger.info(f"Formatted Response: {formatted_response}")
        return formatted_response
    except Exception as e:
        logger.error(f"Error processing AI response: {e}")
        return {"error": str(e)}

def handle_message(channel, method, properties, body, config):
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

        prompt = setupPrompt(userinfo, agentlocation, userlocation, config)
        logger.info(f"Prompt: {prompt}")

        llm = ChatOpenAI(model="gpt-4")
        logger.info(f"LLM: {llm}")

        agent = create_tool_calling_agent(llm, tools, prompt)
        logger.info(f"Agent: {agent}")
        logger.info("=======================================")

        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        logger.info(f"Agent Executor: {agent_executor}")
        logger.info("=======================================")

        try:
            message_history = RedisChatMessageHistory(
                url="redis://default:aKo1aAx6uSMFIKG0v0EYLDH5sOf9zFSR@redis-15294.c56.east-us.azure.redns.redis-cloud.com:15294", ttl=100, session_id=session_id
            )
        except Exception as e:
            logger.error(f"Error setting up message history: {e}")
            return

        logger.info(f"Message History: {message_history}")
        logger.info("=======================================")

        try:
            agent_with_chat_history = RunnableWithMessageHistory(
                agent_executor,
                lambda session_id: message_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
        except Exception as e:
            logger.error(f"Error setting up agent with chat history: {e}")
            return

        try:
            response = agent_with_chat_history.invoke(
                {"input": f"{userquestion}"},
                config={"configurable": {"session_id": session_id}},
            )
        except Exception as e:
            logger.error(f"Error invoking agent with chat history: {e}")
            return

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
        # if config['agent_name'] == 'assessment' and actions(userlocation, userquestion, response):
        #     forward_message(channel, config['queues']['forward'], config['queues']['forward_route'], message)
        # elif config['agent_name'] == 'quality' and actions(userlocation, userquestion, response):
        #     forward_message(channel, config['queues']['forward'], config['queues']['forward_route'], message)
        # elif config['agent_name'] == 'master':
        #     logger.info("Master agent does not forward messages")

    except json.JSONDecodeError:
        logger.error("Received message is not in JSON format. Here is the raw message:")
        logger.error(body.decode('utf-8'))  # Decode and print the raw message as text
    except Exception as e:
        logger.error(f"Error handling message: {e}")
    finally:
        channel.basic_ack(delivery_tag=method.delivery_tag)

def connect_and_consume(agent_name):
    while True:
        try:
            # Load the agent-specific configuration
            config = load_config(agent_name)

            # Load RabbitMQ credentials from environment variables
            rabbitmq_user = os.getenv('RABBITMQ_USER')
            rabbitmq_pass = os.getenv('RABBITMQ_PASS')
            rabbitmq_host = os.getenv('RABBITMQ_HOST')
            rabbitmq_port = int(os.getenv('RABBITMQ_PORT'))

            if not rabbitmq_user or not rabbitmq_pass or not rabbitmq_host or not rabbitmq_port:
                logger.error("RabbitMQ configuration is missing in the environment variables.")
                sys.exit(1)

            # Set up RabbitMQ connection and channel
            credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
            parameters = pika.ConnectionParameters(
                host=rabbitmq_host, 
                port=rabbitmq_port, 
                credentials=credentials,
                heartbeat=60,  # Set heartbeat to 1 minutes
                blocked_connection_timeout=600  # Set blocked connection timeout to 10 minutes
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # Set up the consumer for the listen queue
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
