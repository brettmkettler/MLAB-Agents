# Python Script with YAML Integration

###############################
# Installation to Ubuntu 24
#
# sudo apt install git
# git clone https://github.com/brettmkettler/MLAB-Agents.git
# cd MLAB-Agents/
# sudo apt install python3-venv 
# python3 -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt
# nano .env #insert passwords

# python AMQP_ai_agent_autogen.py <agent>

############################
# Setup Service

# sudo nano /etc/systemd/system/mlab-agent.service

# [Unit]
# Description=MLAB Agent Service
# After=network.target

# [Service]
# User=agent        
# Group=agent         
# WorkingDirectory=/home/agent/MLAB-Agents
# ExecStart=/home/agent/MLAB-Agents/venv/bin/python /home/agent/MLAB-Agents/AMQP_ai_agent_autogen.py quality
# Restart=always

# [Install]
# WantedBy=multi-user.target

# ################
# #Start Service
# sudo systemctl daemon-reload
# sudo systemctl enable mlab-agent.service

# sudo systemctl start mlab-agent.service

# ###############
# Check Status
# sudo systemctl status mlab-agent.service

#################
# Stop Service
# sudo systemctl stop mlab-agent.service

#################
# Update Code
# sudo systemctl stop mlab-agent.service
# git pull origin main
# sudo systemctl restart mlab-agent.service
# sudo journalctl -u mlab-agent.service -f



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
from typing import Optional, Type, List

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

#capgeminiDocumentsTool, ##
from agent_tools import CallTool, capgeminiDocumentsTool, actionTool, Agent2AgentTool, makeCall
from mlab_robots_tools import get_station_overview, get_robot_status, get_robot_programs, send_program_to_robot, GetStationOverview, GetRobotStationStatusOverview, RunFANUC
from agent_llm import run_agent
from langchain_groq import ChatGroq

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

def load_tools(tool_names: List[str]) -> List[BaseTool]:
    """Load tools based on their names."""
    tool_map = {
        "GetStationOverview()": GetStationOverview,
        "CallTool()": CallTool,
        "capgeminiDocumentsTool()": capgeminiDocumentsTool,
        "Agent2AgentTool()": Agent2AgentTool,
        "GetRobotStationStatusOverview()": GetRobotStationStatusOverview,
        "RunFANUC()": RunFANUC,
    }
    tools = []
    for tool_name in tool_names:
        # Ensure the tool name ends with ()
        tool_name_with_parens = tool_name.strip()
        if not tool_name_with_parens.endswith("()"):
            tool_name_with_parens += "()"
        
        tool_class = tool_map.get(tool_name_with_parens)
        if tool_class:
            tools.append(tool_class())
        else:
            logger.warning(f"Tool {tool_name} is not recognized and will be skipped.")
    
    print("Tools: ", tools)
    return tools


# NOTE: change verbiage to send instead of forward
def forward_message(channel, forward_queue, forward_route, message):
    """Send a message to the specified queue."""
    try:
        channel.basic_publish(
            exchange='amq.topic',
            routing_key=forward_route,
            body=json.dumps(message)
        )
        logger.info(f"Message forwarded to {forward_queue} via route {forward_route}.")
    except Exception as e:
        logger.error(f"Failed to forward message: {e}")



def setupPrompt(userinfo, agentlocation, agentprompt):
    
    print ("setting up prompt")
    
    return ChatPromptTemplate.from_messages(
    [
        (
            "system",
            agentprompt,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)
    
####

def process_ai_response(response):
    """Process the AI response to extract actions."""
    try:
        if isinstance(response, str):
            logger.info(f"Raw AI Response: {response}")

            action_pattern = r'"action": "(\w+)", "content": "([^"]*)"'
            actions = re.findall(action_pattern, response)

            if not actions:
                summary = f"""
                "action": "GOTO", "content": "None"
                "action": "POINTAT", "content": "None"
                "action": "TALK", "content": "{response}"
                """
                
                formatted_summary = process_ai_response(summary)
                
                return formatted_summary
            

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
        print("Message Body: ", body)
        message_dict = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Received message is not in JSON format. Here is the raw message:")
        logger.error(body.decode('utf-8'))

        
    

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

            config = load_config(agent_name)
            agent_prompt = config['prompts']['system'].format(userinfo=userinfo, agentlocation=agentlocation, userlocation=userlocation)

            # Tools
            config["tools"] = load_tools(config.get("tools", []))
            tools = config["tools"]
            
            llm = ChatGroq(model="llama-3.1-70b-versatile",
            temperature=0.5,
            max_tokens=None,
            timeout=None,
            max_retries=2)
            
            
            session_id = userinfo

            print("User Info: ", userinfo)
            print("User Location: ", userlocation)
            print("Agent Location: ", agentlocation)
            print("User Question: ", userquestion)
            
            prompt = setupPrompt(userinfo, agentlocation, agent_prompt)
            

            # Construct the Tools agent
            agent = create_tool_calling_agent(llm, tools, prompt)

            print("Agent: ", agent)
            
            print("=======================================")
            print("")
            
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

            print("Agent Executor: ", agent_executor)
            print("=======================================")
            print("")
            
            message_history = RedisChatMessageHistory(
                        url="redis://default:aKo1aAx6uSMFIKG0v0EYLDH5sOf9zFSR@redis-15294.c56.east-us.azure.redns.redis-cloud.com:15294", ttl=500, session_id=session_id
            
            )
            

                            
            print("Message History: ", message_history)

            print("m=======================================")
            print("")
            
            agent_with_chat_history = RunnableWithMessageHistory(
                agent_executor,
                # This is needed because in most real world scenarios, a session id is needed
                # It isn't really used here because we are using a simple in memory ChatMessageHistory
                lambda session_id: message_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )

            try:
                response = agent_with_chat_history.invoke(
                    {"input": f"{userquestion}"},
                    # This is needed because in most real world scenarios, a session id is needed
                    # It isn't really used here because we are using a simple in memory ChatMessageHistory
                    config={"configurable": {"session_id": session_id}},
                )
            except Exception as e:
                return {"error": str(e)}
            

            
            # print to console
            print(response)
            
   
            
            logger.info(f"Raw AI response: {response}")
            
            response = response['output']
            
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
            
            To store memory, you need to use the MEMORY tool.
            
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
