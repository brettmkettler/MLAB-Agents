from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from autogen.function_utils import get_function_schema
from autogen.agentchat.contrib.capabilities.teachability import Teachability

from openai import OpenAI
import logging
import os
from dotenv import load_dotenv
from autogen import UserProxyAgent, config_list_from_json
from typing import Any, Dict, Optional

from agent_tools import actions, makeCall, search_tavily


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

############################################
# FUNCTIONS 
# # NOTE: Move to tools later

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


###############################
# Call Tool

def callTool(question: str) -> str:
    """
    Ability to call and talk to Brett Kettler to ask questions or get information on things you dont know.
    """
    
    print("Running call tool")
    response = makeCall(question)
    print(f"Response: {response}")
    return "The message was sent to the agent."
   

callTool_api_schema = get_function_schema(
    callTool,
    name="callTool",
    description="Ability to call and talk to Brett Kettler to ask questions or get information on things you dont know.",
)

###############################
# SEARCH TOOL

def searchTool(question: str) -> str:
    """
    Ability to search the web for information on things you dont know.
    """
    
    print("Running call tool")
    response = search_tavily(question, search_depth="basic", include_images=False, include_answer=True, include_raw_content=False, max_results=5, include_domains=None, exclude_domains=None)
    print(f"Response: {response}")
    return "The message was sent to the agent."
   

searchTool_api_schema = get_function_schema(
    searchTool,
    name="searchTool",
    description="Ability search the web for information on things you dont know.",
)


# Create the agent
assistant_id = os.environ.get("ASSISTANT_ID", None)

def run_agent(agent_name: str, userquestion: str, prompt: str) -> str:
    """
    Run the agent with the user question.
    """
    
    agent = GPTAssistantAgent(
        name=agent_name,
        # instructions="""You are a working agent in a Capgemini Digital Twin Factory named ai_master. 
        
        # You are a friendly assistant agent that can help answer questions about the lab and the AI models.
        
        # You can ask questions to other agents using the agent2agent API, The other agents are: 
        
        # 1. ai_master - ai_master is the master agent that can answer questions about the factory and its operations or the temperature of the lab.
        # 2. ai_assistant - ai_assistant is the assistant agent that can answer questions about the AI models and their capabilities.
        
        # """,
        instructions=prompt,
        
        overwrite_instructions=True,  # overwrite any existing instructions with the ones provided
        overwrite_tools=True,  # overwrite any existing tools with the ones provided
        llm_config={
            "config_list": config_list,
            # "tools": [agent2agent_api_schema],
            "tools": [callTool_api_schema, searchTool_api_schema],
            "assistant_id": assistant_id,
        },
        verbose=True,
    )

    # Register the function to the agent
    # agent.register_function(function_map={"agent2agent_comm": agent2agent_comm})
    
    agent.register_function(function_map={"callTool": callTool})
    agent.register_function(function_map={"searchTool": searchTool})

    # Update the assistant (ensure that the assistant_id is correctly set in the environment variables)
    if assistant_id:
        client.beta.assistants.update(
            assistant_id=agent.assistant_id,
        )
        

    # Teachability capability
    teachability = Teachability(
        verbosity=2,  # 0 for basic info, 1 to add memory operations, 2 for analyzer messages, 3 for memo lists.
        reset_db=True,
        path_to_db_dir="./tmp/notebook/teachability_db",
        recall_threshold=1.5,  # Higher numbers allow more (but less relevant) memos to be recalled.
    )
    
    teachability.add_to_agent(agent)

    # User proxy for chat
    user_proxy = UserProxyAgent(
        name="user_proxy",
        code_execution_config={"work_dir": "coding", "use_docker": False},
        is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
    )

    chatmessage = user_proxy.initiate_chat(agent, message=userquestion, clear_history=True)

    last_message = chatmessage.chat_history[-1]['content']

    print(f"Last message: {last_message}")

    return last_message
