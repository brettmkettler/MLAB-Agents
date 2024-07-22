import random
from agent_mq import Agent
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the assembly agent
assembly_agent = Agent(
    name="ai_assembly",
    exchange="agent_exchange",
    routing_key="ai_assembly",
    queue="ai_assembly_queue",
    user=os.getenv("AI_USER"),
    password=os.getenv("AI_PASS")
)

# Start receiving messages
assembly_agent.start_receiving()

# Blocking loop to keep the script running
while True:
    pass
