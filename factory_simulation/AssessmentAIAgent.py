import random
from agent import Agent
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the assessment agent
assessment_agent = Agent(
    name="ai_assessment",
    exchange="agent_exchange",
    routing_key="ai_assessment",
    queue="ai_assessment_queue",
    user=os.getenv("AI_USER"),
    password=os.getenv("AI_PASS")
)

# Start receiving messages
assessment_agent.start_receiving()

# Blocking loop to keep the script running
while True:
    pass
