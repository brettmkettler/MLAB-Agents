from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from autogen.function_utils import get_function_schema

from openai import OpenAI
import logging
import os
from dotenv import load_dotenv
from autogen import UserProxyAgent, config_list_from_json
from typing import Any, Dict, Optional

from agent_tools import agent2agent_comm

# Load environment variables
load_dotenv()

# OpenAI API
client = OpenAI()

# Configuration for the agent
config_list = config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    file_location=".",
    filter_dict={
        "model": ["gpt-4o"],
    },
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

def agent2agent_comm(fromagent: str, agent: str, question: str) -> str:
    """
    Ability to talk to another agent to ask questions or get information.
    """
    
    print("Running agent2agent_comm")
    
    print(f"From Agent: {fromagent}")
    print(f"Agent: {agent}")
    print(f"Question: {question}")
    
    response = agent2agent_comm(fromagent, agent, question)
    print(f"Response: {response}")
    
    return "The message was sent to the agent."
    

agent2agent_api_schema = get_function_schema(
    agent2agent_comm,
    name="agent2agent_comm",
    description="Ability to talk to another agent to ask questions or get information.",
)

# Create the agent
assistant_id = os.environ.get("ASSISTANT_ID", None)

cap_phil = GPTAssistantAgent(
    name="ai_assessment",
    instructions="""You are a working agent in a Capgemini Digital Twin Factory named ai_assessment. You can ask questions to other agents using the agent2agent API. 
    The other agents are: 
    
    1. ai_master - ai_master is the master agent that can answer questions about the factory and its operations or the temperature of the lab.
    2. ai_assistant - ai_assistant is the assistant agent that can answer questions about the AI models and their capabilities.
    
    """,
    overwrite_instructions=True,  # overwrite any existing instructions with the ones provided
    overwrite_tools=True,  # overwrite any existing tools with the ones provided
    llm_config={
        "config_list": config_list,
        "tools": [agent2agent_api_schema],
        "assistant_id": assistant_id,
    },
    verbose=True,
)

# Register the function to the agent
cap_phil.register_function(function_map={"agent2agent_comm": agent2agent_comm})

# Update the assistant (ensure that the assistant_id is correctly set in the environment variables)
if assistant_id:
    client.beta.assistants.update(
        assistant_id=cap_phil.assistant_id,
    )

# User proxy for chat
user_proxy = UserProxyAgent(
    name="user_proxy",
    code_execution_config={"work_dir": "coding", "use_docker": False},
    is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
)

def run_agent(agent_name: str, data: str, userinfo: str, userlocation: str, agentlocation: str) -> str:
    """
    Run the agent with the user question.
    """
    userquestion = data

    chatmessage = user_proxy.initiate_chat(cap_phil, message=userquestion, clear_history=True)

    last_message = chatmessage.chat_history[-1]['content']

    print(f"Last message: {last_message}")

    return last_message
