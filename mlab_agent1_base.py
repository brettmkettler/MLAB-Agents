import logging
import os
import requests
import autogen
from autogen import UserProxyAgent, config_list_from_json

# from autogen.agentchat import UserProxyAgent
from autogen.agentchat.contrib.capabilities.teachability import Teachability
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from openai import OpenAI

# Azure Service Bus
from azure.servicebus import ServiceBusClient, ServiceBusMessage

# Create a UserProxyAgent
from dotenv import load_dotenv
load_dotenv()

# OpenAI API
client = OpenAI()

# Azure Service Bus
connection_string = os.getenv('AZURE_SERVICE_BUS_CONNECTION_STRING')
queue_name_agent_1 = os.getenv('QUEUE_NAME_AGENT_1')
queue_name_agent_2 = os.getenv('QUEUE_NAME_AGENT_2')


######## CUSTOM CLASSES

config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    file_location=".",
    filter_dict={
        "model": ["gpt-4o", "gpt-4-1106-preview", "gpt4", "gpt-4-32k"],
    },
)



#############

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
    "description": "This is an API endpoint allowing users (analysts) to input question about GitHub in text format to retrieve the realted and structured data.",
}


def get_ossinsight(question):
    """
    Retrieve the top 10 developers with the most followers on GitHub.
    """
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
  







########### CREATE AGENT






assistant_id = os.environ.get("ASSISTANT_ID", None)

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
    instructions=(
        "You are a working agent in a Capgemini Digital Twin Factory named Phil."
    ),
    llm_config=llm_config,
    verbose=True,
)

print(cap_phil)

# print the assistant id
print("Assistant ID", cap_phil.assistant_id)

assistant_id = cap_phil.assistant_id

print("Agent created.")





#### ADD FUNCTION TO AGENT
cap_phil.register_function(
    function_map={
        "ossinsight_data_api": get_ossinsight,
    }
)






# Update the agents file search

vector_store_id = os.environ.get("VECTOR_STORE_ID")



tool_resources = {
    "file_search": {
        "vector_store_ids": [vector_store_id]
    }
}

# Update the assistant with the correct tool resources structure
client.beta.assistants.update(
  assistant_id=assistant_id,
  tool_resources=tool_resources,
)






########### GIVE AGENT TASK ###############



user_proxy = UserProxyAgent(
    name="user_proxy",
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
    },  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
    is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
)

# Add the UserProxyAgent to the Teachability capability


teachability = Teachability(reset_db=False, llm_config={"config_list": config_list})
teachability.add_to_agent(cap_phil)



###########################


# Console chat loop
def console_chat():
    print("Chat initialized. Type 'exit' to terminate the chat.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Terminating chat.")
            break

        user_proxy.initiate_chat(cap_phil, message=user_input, clear_history=False)

console_chat()
