import os
from agent import Agent
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

master_agent = Agent(
    name="MasterAgent",
    exchange="agent_exchange",
    routing_key="master",
    queue="master_queue",
    user=os.getenv('AI_USER'),
    password=os.getenv('AI_PASS')
)
master_agent.start_receiving()
