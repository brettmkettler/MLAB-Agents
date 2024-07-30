import json
import os
from typing import Literal
from typing_extensions import Annotated
import autogen
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from autogen.function_utils import get_function_schema
from autogen.agentchat.contrib.capabilities.teachability import Teachability

from httpx import get
from openai import OpenAI
import logging
import os
from dotenv import load_dotenv
from autogen import AssistantAgent, ConversableAgent, UserProxyAgent, config_list_from_json
from typing import Any, Dict, Optional

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun

from OLD_USABLE.app import Chat
from agent_tools import actions, makeCall, search_tavily, tavily

from mlab_robots_tools import get_station_overview, get_robot_status, get_robot_programs, send_program_to_robot, GetStationOverview


# Load environment variables
load_dotenv()

# OpenAI API
client = OpenAI()

# Configuration for the agent

# config_list = [
#     {
#         # Let's choose the Llama 3 model
#         "model": "llama3-8b-8192",
#         "base_url": "https://api.groq.com/openai/v1",
#         # Put your Groq API key here or put it into the GROQ_API_KEY environment variable.
#         "api_key": os.environ.get("GROQ_API_KEY"),
#         # We specify the API Type as 'groq' so it uses the Groq client class
#         "api_type": "groq",
        
#         "cache_seed": None
#     }
# ]

prompt_price_per_1k=0
completion_token_price_per_1k=0
config_list= [{"model": "llama3-70b-8192", "api_key": os.environ.get("GROQ_API_KEY"), "base_url": "https://api.groq.com/openai/v1", "price": [prompt_price_per_1k, completion_token_price_per_1k], "frequency_penalty": 0.5, "max_tokens": 2048, "presence_penalty": 0.2, "temperature": 0.5, "top_p": 0.2}]
llm_config = {"config_list":config_list}

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

############################################
# FUNCTIONS 
# # NOTE: Move to tools later

# MLAB OVERVIEW


getoverview_api_schema = get_function_schema(
    get_station_overview,
    name="get_station_overview",
    description="Ability to get the overview of all stations and robots in the lab.",
)



#
#
#


# AGENT2AGENT COMMUNICATION
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
    Ability to call and talk to Brett Kettler to update him on the lab. Only use this for emergencies.
    """
    
    print("Running call tool")
    response = makeCall(question)
    print(f"Response: {response}")
    # reformat the response to string
    response = str(response)
    return response
   

callTool_api_schema = get_function_schema(
    callTool,
    name="callTool",
    description="Ability to call and talk to Brett Kettler. Only use this for emergencies do not call unless there is an absolute emergency.",
)

###############################
# SEARCH TOOL

def searchTool(question: str) -> str:
    """
    Ability to search the web for information to search for things you do not know.
    """
    
    print("Running call tool")
    #response = tavily(question)
    from langchain_community.tools import DuckDuckGoSearchResults

    search = DuckDuckGoSearchResults()
    
    # search = DuckDuckGoSearchRun()

    response = search.invoke(question)
    
    print(f"Response: {response}")
    # reformat the response to string
    response = response["results"]
    
    return response
   

searchTool_api_schema = get_function_schema(
    searchTool,
    name="searchTool",
    description="Ability search the web for information on things you dont know.",
)


# Create the agent
assistant_id = os.environ.get("ASSISTANT_ID", None)

tools = [GetStationOverview()]

def run_agent(agent_name: str, userquestion: str, prompt: str) -> str:
    """
    Run the agent with the user question.
    """
    

    llm = ChatGroq(model="llama3-70b-8192",
    temperature=0.5,
    max_tokens=None,
    timeout=None,
    max_retries=2)
    
    prompt1 = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                prompt,
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    # Construct the Tools agent
    agent = create_tool_calling_agent(llm, tools, prompt1)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    response = agent_executor.invoke({"input": userquestion})
    
    last_message = response["output"]
    
    # print(f"Message: {message}")

    return last_message
