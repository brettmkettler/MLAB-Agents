import os
from agent import Agent
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

assembly_agent = Agent(
    name="AssemblyAgent",
    exchange="agent_exchange",
    routing_key="assembly",
    queue="assembly_queue",
    user=os.getenv("AI_USER"),
    password=os.getenv("AI_PASS")
)
assembly_agent.start_receiving()
