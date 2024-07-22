import random
from agent import Agent
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the assembly agent
master_agent = Agent(
    name="ai_master",
    exchange="agent_exchange",
    routing_key="ai_master",
    queue="ai_master_queue",
    user=os.getenv("AI_USER"),
    password=os.getenv("AI_PASS")
)

# Start receiving messages
master_agent.start_receiving()

# Blocking loop to keep the script running
while True:
    pass
