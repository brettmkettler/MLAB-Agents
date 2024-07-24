import logging
import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from agent_tools import Tools

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def run_agent(agent_name, userquestion, prompt):
    tools = Tools()
    agent = AgentExecutor(
        name=agent_name,
        instructions=prompt,
        tools=[tools.capgemini_documents_tool, tools.action_tool],
        verbose=True,
    )
    
    response = agent.run(userquestion)
    return response
