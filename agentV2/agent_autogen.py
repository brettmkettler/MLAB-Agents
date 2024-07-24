import glob
import sys
import yaml
import json
import re
import time
import os
import logging
import pika
import ssl
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Type
from agent_communication import Communication
from agent_tools import Tools, CapgeminiDocumentsTool, ActionTool
from agent_llm import run_agent

from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings, ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationBufferMemory

from agent_tools import CapgeminiDocumentsInputs, CallTool, ActionTool, Agent2AgentTool, makeCall
from agent_llm import run_agent

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.config = self.load_config(agent_name)
        self.comm = Communication(self.config)
        self.tools = Tools()
    
    def load_config(self, agent_name):
        config_file = f"./config/{agent_name}.yaml"
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        return config
    
    def setup_prompt(self, userinfo, agentlocation, userlocation):
        logger.info("Setting up prompt")
        return ChatPromptTemplate.from_messages([
            ("system", self.config['prompts']['system'].format(
                userinfo=userinfo, 
                agentlocation=agentlocation, 
                userlocation=userlocation)
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
    
    def process_ai_response(self, response):
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
                    if (action_type := action_type.upper()) in action_types:
                        action_types[action_type] = action_content

                actions_list = [{"action": k, "content": v} for k, v in action_types.items()]
                formatted_response = {"response": actions_list}
                logger.info(f"Formatted Response: {formatted_response}")
                return formatted_response
            else:
                logger.warning("No valid response from the AI.")
                return {"error": "No valid response from the AI."}
        except Exception as e:
            logger.error(f"Error processing AI response: {e}")
            return {"error": str(e)}
    
    def handle_message(self, channel, method, properties, body):
        logger.info(f"Received raw message: {body}")
        try:
            message = json.loads(body)
            userquestion = message.get('userquestion', 'No question provided')
            userinfo = message.get('user_id', 'Unknown user')
            userlocation = message.get('user_location', 'Unknown location')
            agentlocation = message.get('agent_location', 'Unknown location')

            logger.info(f"User Info: {userinfo}")
            logger.info(f"User Location: {userlocation}")
            logger.info(f"Agent Location: {agentlocation}")
            logger.info(f"User Question: {userquestion}")

            prompt = self.setup_prompt(userinfo, agentlocation, userlocation)
            prompt = str(prompt)
            logger.info(f"Prompt: {prompt}")

            response = run_agent(self.agent_name, userquestion, prompt)
            logger.info(f"Raw AI response: {response}")
            formatted_response = self.process_ai_response(response)

            self.comm.send_message(formatted_response, self.config['queues']['publish_route'])
        except json.JSONDecodeError:
            logger.error("Received message is not in JSON format. Here is the raw message:")
            logger.error(body.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
        finally:
            channel.basic_ack(delivery_tag=method.delivery_tag)
    
    def connect_and_consume(self):
        while True:
            try:
                self.comm.setup_connection()
                self.comm.channel.basic_consume(queue=self.config['queues']['listen'], on_message_callback=self.handle_message)
                logger.info(f'Waiting for messages from "{self.config["queues"]["listen"]}". To exit press CTRL+C')
                self.comm.channel.start_consuming()
            except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelError) as e:
                logger.error(f"Connection error: {e}. Reconnecting in 10 seconds...")
                time.sleep(10)
            except Exception as e:
                logger.error(f"Unexpected error: {e}. Reconnecting in 10 seconds...")
                time.sleep(10)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.error("Usage: python agent_autogen.py <agent_name>")
        sys.exit(1)
    agent_name = sys.argv[1]
    agent = Agent(agent_name)
    agent.connect_and_consume()
