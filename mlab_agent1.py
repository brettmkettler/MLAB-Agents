import os
import logging
import requests
import threading
import time
import json
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from autogen import UserProxyAgent, config_list_from_json
from autogen.agentchat.contrib.capabilities.teachability import Teachability
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from openai import OpenAI
import base64
from serviceBus2 import AzureServiceBusDictManager  # Import the class

# Load environment variables
load_dotenv()

# OpenAI API
client = OpenAI()

# Debug prints
connection_string = os.getenv('AZURE_SERVICE_BUS_CONNECTION_STRING')
topic_name = os.getenv('TOPIC_NAME')
subscription_name_agent_1 = os.getenv('SUBSCRIPTION_NAME_AGENT_1')

print("Connection String:", connection_string)
print("Topic Name:", topic_name)
print("Subscription Name Agent 1:", subscription_name_agent_1)

# Custom classes and configurations
config_list = config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    file_location=".",
    filter_dict={
        "model": ["gpt-4o", "gpt-4-1106-preview", "gpt4", "gpt-4-32k"],
    },
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

ossinsight_api_schema = {
    "name": "ossinsight_data_api",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": (
                    "Enter your GitHub data question in the form of a clear and specific question to ensure the returned data is accurate and valuable. "
                    "For optimal results, specify the desired format for the data table in your request."
                ),
            }
        },
        "required": ["question"],
    },
    "description": "This is an API endpoint allowing users (analysts) to input question about GitHub in text format to retrieve the related and structured data.",
}

def get_ossinsight(question):
    url = "https://api.ossinsight.io/explorer/answer"
    headers = {"Content-Type": "application/json"}
    data = {"question": question, "ignoreCache": True}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        answer = response.json()
    else:
        return f"Request to {url} failed with status code: {response.status_code}"

    report_components = []
    report_components.append(f"Question: {answer['question']['title']}")
    if answer["query"]["sql"] != "":
        report_components.append(f"querySQL: {answer['query']['sql']}")

    if answer.get("result", None) is None or len(answer["result"]["rows"]) == 0:
        result = "Result: N/A"
    else:
        result = "Result:\n  " + "\n  ".join([str(row) for row in answer["result"]["rows"]])
    report_components.append(result)

    if answer.get("error", None) is not None:
        report_components.append(f"Error: {answer['error']}")
    return "\n\n".join(report_components) + "\n\n"

# Create agent
assistant_id = os.getenv("ASSISTANT_ID", None)

config_list = config_list_from_json("OAI_CONFIG_LIST")

llm_config = {
    "config_list": config_list,
    "assistant_id": assistant_id,
    "tools": [
        {"type": "file_search"},
        {
            "type": "function",
            "function": ossinsight_api_schema,
        }
    ],
}

cap_phil = GPTAssistantAgent(
    name="Cap_Phil",
    instructions="You are a working agent in a Capgemini Digital Twin Factory named Phil.",
    llm_config=llm_config,
    verbose=True,
)

print(cap_phil)
print("Assistant ID", cap_phil.assistant_id)

cap_phil.register_function(
    function_map={
        "ossinsight_data_api": get_ossinsight,
    }
)

vector_store_id = os.getenv("VECTOR_STORE_ID")

tool_resources = {
    "file_search": {
        "vector_store_ids": [vector_store_id]
    }
}

client.beta.assistants.update(
    assistant_id=cap_phil.assistant_id,
    tool_resources=tool_resources,
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
    },
    is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
)

teachability = Teachability(reset_db=True, llm_config={"config_list": config_list})
teachability.add_to_agent(cap_phil)

# Initialize AzureServiceBusDictManager
agentMsg = AzureServiceBusDictManager()

def listen_to_subscription(subscription_name, agent):
    while True:
        try:
            # List messages in the subscription
            messages = agentMsg.list_all_messages_in_subscription(topic_name, subscription_name) or []
            for message in messages:
                # Process the message
                user_input = message['body']
                if isinstance(user_input, bytes):
                    user_input = user_input.decode('utf-8')
                user_input = json.loads(user_input)  # Assuming the message is a JSON string
                chat_result = user_proxy.initiate_chat(agent, message=user_input, clear_history=True, summary_method="reflection_with_llm")
                
                # Send the chat result back to the topic
                response_message = {
                    "response": chat_result
                }
                response_properties = {"topic": "response"}
                agentMsg.send_message_to_topic(topic_name, response_message, response_properties)
        
        except Exception as e:
            logger.error(f"Error while processing messages: {e}")
        
        time.sleep(5)  # Polling interval

# Listen to subscriptions in separate threads
agent_1_thread = threading.Thread(target=listen_to_subscription, args=(subscription_name_agent_1, cap_phil))

agent_1_thread.start()
